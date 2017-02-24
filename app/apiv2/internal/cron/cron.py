from datetime import datetime, timedelta
from flask import current_app, url_for
from flask_restful import Resource
from sqlalchemy.sql import func, and_, desc, or_
from sqlalchemy import text as sqltext

import requests

from app import db, constants
from app.models import Organization, Schedule2, Shift2, Location, Role, \
    Timeclock, User
from app.plans import boss_plans
from app.caches import IncidentCache
from app.helpers import get_default_tz, normalize_to_midnight

from app.apiv2.decorators import permission_sudo
from app.apiv2.email import alert_email

from app.apiv2.internal.cron.cron_timeclock_notification_sms import run_cron_timeclock_notification_sms


class ShiftMechanic(Resource):
    """ Cron job runner on Staffjoy states """

    @permission_sudo
    def get(self):
        results = {}

        # Deactivate free trials that expired
        self._deactivate_expired_organizations()

        # Schedule Creation and Promotion
        results["schedules_created"] = self._create_schedules()
        results["schedules_queued_mobius"] = self._enqueue_schedules_mobius()

        # Cleanup
        self._close_abandoned_timeclocks()

        # Monitoring
        self._monitor_active_incidents()
        self._monitor_schedules_queued_too_long()
        self._monitor_chomp_processing_too_long()
        self._monitor_mobius_processing_too_long()
        self._verify_shift_schedule_published_parity()

        # Notifications
        run_cron_timeclock_notification_sms()

        current_app.logger.debug("Cron results: %s" % results)
        return results, 200

    def _deactivate_expired_organizations(self):
        orgs_to_deactivate = Organization.query\
            .filter_by(active=True)\
            .filter(
                and_(
                    or_(
                        Organization.paid_until == None,
                        Organization.paid_until < func.now()
                    ),
                    func.timestampdiff(
                        sqltext("SECOND"),
                        Organization.created_at,
                        func.now(),
                    ) > (Organization.trial_days * constants.SECONDS_PER_DAY),
                )
            )

        for org in orgs_to_deactivate:
            manager_url = url_for(
                'manager.manager_app', org_id=org.id,
                _external=True) + "#settings"

            # alert admins of deactivation
            for admin in org.admins:
                alert_email(
                    admin,
                    "[Action Required] %s scheduling is on hold" % org.name,
                    "In order to continue scheduling, please set up billing at:<br><a href='%s'>%s</a>"
                    % (manager_url, manager_url))

            org.active = False
            current_app.logger.info(
                "Deactivated org %s because it is unpaid and the trial is over"
                % org.id)
            db.session.commit()

    def _create_schedules(self):
        """ Create schedules for active orgs """

        default_tz = get_default_tz()

        # Approach - Start with Roles. Join to Org so you know
        # how much lead time for a schedule (demand_opends_days_before_start).
        # Then, OUTER (left) join to Schedules. Look for schedules that
        # are IN the window of that lead time. Then, becuase it's an OUTER join,
        # filter by role IDs that do NOT have a schedule in that window. 
        # You are left with roles that need a schedule to be 
        # created in that window.

        roles_needing_schedules = Role.query\
            .join(Location)\
            .join(Organization)\
            .outerjoin(Schedule2,
                and_(
                    Role.id == Schedule2.role_id,
                    # Convert to seconds to do this math. Note that `time-to-sec` is mysql-specific
                    func.timestampdiff(
                        sqltext("SECOND"),
                        func.now(),
                        Schedule2.start,
                    # If not offset by 7 - start a week early
                    ) > current_app.config.get("SCHEDULES_CREATED_DAYS_BEFORE_START") * constants.SECONDS_PER_DAY,
                ),
            )\
            .filter(
                Organization.active == True,
                Role.archived == False,
                Schedule2.id == None,
            ).all()

        schedules_created = 0  # for return

        # Make schedules until horizon for all roles that need them
        start = None
        schedule_horizon = default_tz.localize(datetime.utcnow() + timedelta(
            days=current_app.config.get(
                "SCHEDULES_CREATED_DAYS_BEFORE_START")))

        # This is a half year of schedules.
        # We discovered that during the apiv1 migration, some orgs only had a couple weeks
        # worth of schedules. When _get_schedule_range() ran, it would get the dates for the next
        # schedule. This requires a high ttl because it is making schedules in the past up to
        # the 100 days in the future that we expect.
        schedule_ttl = 27
        for role in roles_needing_schedules:

            start, stop = self._get_schedule_range(role)
            current_ttl = schedule_ttl
            while (start < schedule_horizon):

                current_ttl -= 1
                if current_ttl < 0:
                    raise Exception(
                        "Schedule creation process infinite looping - start %s role %s"
                        % (start, role))

                Schedule2.create(role.id, start, stop)
                schedules_created += 1

                start, stop = self._get_schedule_range(role)

        return schedules_created

    def _get_schedule_range(self, role):
        """
        given a Role object, determines the start/stop of its next schedule

        return: (tuple) start, stop
        """

        org = Organization.query.join(Location)\
            .join(Role).filter(Role.id == role.id).first()

        default_tz = get_default_tz()
        local_tz = role.location.timezone_pytz

        last_schedule = Schedule2.query \
            .filter_by(role_id=role.id) \
            .order_by(desc(Schedule2.start)) \
            .first()

        # schedule exists
        if last_schedule:
            start = default_tz.localize(last_schedule.stop)

        # need to create a start for the 1st schedule
        else:

            now = local_tz.localize(normalize_to_midnight(datetime.utcnow()))

            now_utc = now.astimezone(default_tz)
            week_start_index = constants.DAYS_OF_WEEK.index(
                org.day_week_starts)
            adjust_days = (
                (6 - week_start_index + now.weekday()) % constants.WEEK_LENGTH)

            start = normalize_to_midnight(
                (now_utc - timedelta(days=adjust_days, hours=23)
                 ).astimezone(local_tz)).astimezone(default_tz)

        stop = normalize_to_midnight((start + timedelta(days=constants.WEEK_LENGTH, hours=1)).astimezone(local_tz)) \
            .astimezone(default_tz)

        return start, stop

    def _enqueue_schedules_mobius(self):
        """ find and then queue all schedules that are due for mobius processing """

        schedules_to_queue = Schedule2.query \
            .join(Role) \
            .join(Location) \
            .join(Organization) \
            .filter(
                Schedule2.state.in_(["initial", "unpublished"]),
                Organization.plan.in_(boss_plans),
                Organization.active,
                Role.archived == False,
                func.timestampdiff(
                    sqltext("SECOND"),
                    func.now(),
                    Schedule2.start,
                ) < Organization.shifts_assigned_days_before_start * constants.SECONDS_PER_DAY,
            ).all()

        for s in schedules_to_queue:
            if s.state == "initial":
                s.transition_to_unpublished()

            s.transition_to_mobius_queue()

        return len(schedules_to_queue)  # For monitoring

    def _close_abandoned_timeclocks(self):
        """Close timeclocks if they have been open for more than 23 hours """

        cutoff_start = datetime.utcnow() - timedelta(
            hours=constants.MAX_TIMECLOCK_HOURS)

        timeclocks_to_close = Timeclock.query\
            .filter(
                Timeclock.stop==None,
                cutoff_start > Timeclock.start,
            )\
            .all()

        for timeclock in timeclocks_to_close:
            timeclock.stop = timeclock.start + timedelta(
                hours=constants.MAX_TIMECLOCK_HOURS)
            db.session.commit()
            current_app.logger.info(
                "Closed abandoned timeclock id %s (user %s)" %
                (timeclock.id, timeclock.user_id))

            user = User.query.get(timeclock.user_id)
            alert_email(
                user, "You have been automatically clocked out",
                "You have been clocked in for over %s hours, so you have been automatically clocked out."
                % constants.MAX_TIMECLOCK_HOURS)

            if user.phone_number:
                user.send_sms(
                    "You have been automatically clocked out by Staffjoy after being clocked in for %s hours"
                    % constants.MAX_TIMECLOCK_HOURS)
            role = Role.query.get(timeclock.role_id)
            location = Location.query.get(role.location_id)
            org = Organization.query.get(location.organization_id)

            location.send_manager_email(
                "[Action Required] %s forgot to clock out" % user.name,
                "%s (%s) forgot to clock out of their last shift, so Staffjoy just automatically clocked them out after %s hours. Please review and adjust their timeclock on the %s attendance page."
                % (user.name, user.email, constants.MAX_TIMECLOCK_HOURS,
                   location.name),
                url_for("manager.manager_app", org_id=org.id, _external=True) +
                "#locations/%s/attendance" % location.id)

    def _monitor_active_incidents(self):
        """ Query statuspage.io for active incidents """
        if not current_app.config.get("STATUS_PAGE_ID"):
            current_app.logger.info(
                "unable to monitor active incidents because STATUS_PAGE_ID not configured"
            )
            return

        try:
            r = requests.get(
                "https://api.statuspage.io/v1/pages/%s/incidents/unresolved.json?api_key=%s"
                % (current_app.config.get("STATUS_PAGE_ID"),
                   current_app.config.get("STATUS_PAGE_API_KEY"), ))
            if r.status_code != requests.codes.ok:
                current_app.logger.info(
                    "Failed statuspage.io lookup - code %s" % r.status_code)
                return

            incidents = r.json()
            if len(incidents) > 0:
                current_app.logger.info(
                    "%s active incidents detected from StatusPage" %
                    len(incidents))
                IncidentCache.set("", True)  # Say there is an active incident
            else:
                IncidentCache.delete("")
        except:
            current_app.logger.info("failed to query statuspage")
        return

    def _monitor_schedules_queued_too_long(self):
        """
        check for schedules that have been in the queue for too long
        checks for both chomp and mobius queue
        """

        threshold = datetime.utcnow() - timedelta(
            seconds=current_app.config.get("QUEUE_TIMEOUT"))

        overtime_queue_schedules = Schedule2.query \
            .join(Role)\
            .join(Location)\
            .join(Organization)\
            .filter(
                Organization.active,
                or_(
                    Schedule2.state == "chomp-queue",
                    Schedule2.state == "mobius-queue",
                ),
                threshold  > Schedule2.last_update,
            ).all()

        for schedule in overtime_queue_schedules:

            elapsed = (
                datetime.utcnow() - schedule.last_update).total_seconds() / 60

            current_app.logger.warning(
                "Schedule %s has not started processing. Queued for %s minutes in state %s."
                % (schedule.id, elapsed, schedule.state))

        return

    def _monitor_chomp_processing_too_long(self):
        """ check for chomp schedules that have been processing for too long """

        threshold = datetime.utcnow() - timedelta(
            seconds=current_app.config.get("CHOMP_PROCESSING_TIMEOUT"))

        overtime_chomp_schedules = Schedule2.query \
            .join(Role)\
            .join(Location)\
            .join(Organization)\
            .filter(
                Organization.active,
                Schedule2.state == "chomp-processing",
                threshold > Schedule2.chomp_start,
            ).all()

        for schedule in overtime_chomp_schedules:

            elapsed = (
                datetime.utcnow() - schedule.last_update).total_seconds() / 60

            current_app.logger.warning(
                "Schedule %s has not completed Chomp calculation. Processing for %s minutes."
                % (schedule.id, elapsed))

        return

    def _monitor_mobius_processing_too_long(self):
        """ check for mobius schedules that have been processing for too long """

        threshold = datetime.utcnow() - timedelta(
            seconds=current_app.config.get("MOBIUS_PROCESSING_TIMEOUT"))

        overtime_mobius_schedules = Schedule2.query \
            .join(Role)\
            .join(Location)\
            .join(Organization)\
            .filter(
                Organization.active,
                Schedule2.state == "mobius-processing",
                threshold > Schedule2.mobius_start,
            ).all()

        for schedule in overtime_mobius_schedules:

            elapsed = (
                datetime.utcnow() - schedule.mobius_start).total_seconds() / 60

            current_app.logger.warning(
                "Schedule %s has not completed mobius calculation. Processing for %s minutes."
                % (schedule.id, elapsed))

        return

    def _verify_shift_schedule_published_parity(self):
        """
        before a schedule is published, all shifts inside it cannot be published
        """
        # check unpublished schedules with shifts that are published
        unpublished_schedules_no_parity = Schedule2.query \
            .join(Role) \
            .join(Location) \
            .join(Organization) \
            .join(Shift2) \
            .filter(
                Schedule2.state != "published",
                Schedule2.role_id == Shift2.role_id,
                Shift2.start >= Schedule2.start,
                Shift2.stop < Schedule2.stop,
                Shift2.published == True,
            ).all()

        if len(unpublished_schedules_no_parity) > 0:
            for schedule in unpublished_schedules_no_parity:
                current_app.logger.warning(
                    "Schedule %s is not published but has shifts that are" %
                    schedule.id)
