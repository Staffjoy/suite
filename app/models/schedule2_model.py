from datetime import datetime, timedelta
import json

from flask import current_app, render_template, url_for
from sqlalchemy import ForeignKey, and_, or_, select

from app.caches import Schedules2Cache, Shifts2Cache
from app.helpers import verify_days_of_week_struct
from app import db

import recurring_shift_model  # pylint: disable=relative-import
import shift2_model  # pylint: disable=relative-import
import user_model  # pylint: disable=relative-import
import organization_model  # pylint: disable=relative-import
from app.models.location_model import Location
from app.models.role_model import Role
from app.models.role_to_user_model import RoleToUser


def schedule_require_active(f):
    """ The organization attached to this schedule must be active """

    def decorator(self, *args, **kwargs):
        # Join all the way to the org to figure out whether it is active
        active = db.session.execute(
            select([organization_model.Organization.active]).where(
                Role.id == self.role_id).where(Location.id == Role.location_id)
            .where(organization_model.Organization.id == Location.
                   organization_id).select_from(Role).select_from(Location)
            .select_from(organization_model.Organization)).fetchone()[0]

        if not active:
            raise Exception("Cannot promote schedule of inactive org")

        return f(self, *args, **kwargs)

    return decorator


class Schedule2(db.Model):
    """ introduced for apiv2"""

    VALID_STATES = [
        "initial", "unpublished", "chomp-queue", "chomp-processing",
        "mobius-queue", "mobius-processing", "published"
    ]

    __tablename__ = "schedules2"
    id = db.Column(db.Integer, primary_key=True)
    role_id = db.Column(db.Integer, ForeignKey("roles.id"), nullable=False)
    state = db.Column(
        db.String(256),
        db.Enum("initial", "unpublished", "chomp-queue", "chomp-processing",
                "mobius-queue", "mobius-processing", "published"),
        index=True,
        default="unpublished",
        server_default="unpublished",
        nullable=False)
    demand = db.Column(db.LargeBinary)
    start = db.Column(db.DateTime(), index=True)
    stop = db.Column(db.DateTime(), index=True)

    # chomp schedules
    # 1 unit = 30 minutes
    min_shift_length_half_hour = db.Column(db.Integer)
    max_shift_length_half_hour = db.Column(db.Integer)

    # tracking
    created_at = db.Column(db.DateTime(), default=datetime.utcnow)
    last_update = db.Column(db.DateTime(), onupdate=datetime.utcnow)

    # monitoring
    chomp_start = db.Column(db.DateTime())
    chomp_end = db.Column(db.DateTime())
    mobius_start = db.Column(db.DateTime())
    mobius_end = db.Column(db.DateTime())

    @staticmethod
    def create(role_id,
               start,
               stop,
               state="initial",
               demand=None,
               force_send=False):
        """
        Create and return a new schedule. Don't send notifications.
        Start is a datetime object with pytz UTC as tz_info
        """

        role = Role.query.get(role_id)
        loc = Location.query.get(role.location_id)
        org = organization_model.Organization.query.get(loc.organization_id)

        if not org.active and not force_send:
            raise Exception("Cannot create a schedule of inactive org")

        if state not in Schedule2.VALID_STATES:
            raise Exception("Cannot create a schedule in an invalid state")

        if demand is not None:
            if not verify_days_of_week_struct(demand):
                raise Exception(
                    "Cannot create a schedule with poorly structured demand")
            else:
                demand = json.dumps(demand)

        # cast start to local time
        local_tz = loc.timezone_pytz

        localized_start = start.astimezone(local_tz)
        localized_stop = stop.astimezone(local_tz)

        # Check if correct day of week
        if localized_start.strftime(
                "%A").lower() != org.day_week_starts.lower():
            raise Exception("Schedule starts on incorrect day of week for org")

        # Check if correct day of week
        if localized_stop.strftime(
                "%A").lower() != org.day_week_starts.lower():
            raise Exception("Schedule stops on incorrect day of week for org")

        # check that the local start time is exactly midnight
        if not all(x == 0
                   for x in [
                       localized_start.hour, localized_start.minute,
                       localized_start.second, localized_start.microsecond
                   ]):
            raise Exception(
                "Schedule start is not exactly midnight in local time %s" %
                localized_start)

        # check that the local stop time is exactly midnight
        if not all(x == 0
                   for x in [
                       localized_stop.hour, localized_stop.minute,
                       localized_stop.second, localized_stop.microsecond
                   ]):
            raise Exception(
                "Schedule stop is not exactly midnight in local time %s" %
                localized_stop)

        # the total duration of the week must be between a reasonable min/max (to consider DST changes)
        duration_seconds = (stop - start).total_seconds()
        week_seconds = timedelta(days=7).total_seconds()
        search_window = timedelta(hours=2).total_seconds()
        if not ((week_seconds - search_window) < duration_seconds <
                (week_seconds + search_window)):
            raise Exception(
                "Duration between start and end is incorrect (%s seconds)" %
                duration_seconds)

        # sql alchemy gets grumpy when a timezone is added in with the datetime
        # from here on out, tzinfo will be None, and start/stop are in UTC
        start = start.replace(tzinfo=None)
        stop = stop.replace(tzinfo=None)

        # make query to see if any overlapping schedules - there should be none
        overlapping_schedules = Schedule2.query \
            .filter(
                Schedule2.role_id == role_id,
                or_(
                    and_(
                        Schedule2.start <= start,
                        Schedule2.stop >= stop
                    ),
                    and_(
                        Schedule2.start >= start,
                        Schedule2.start < stop,
                    ),
                    and_(
                        Schedule2.stop > start,
                        Schedule2.stop <= stop
                    )
                )
            ).all()

        if len(overlapping_schedules) > 0:
            raise Exception(
                "Overlapping schedule found for role id %s between %s and %s" %
                (role_id, start, stop))

        schedule = Schedule2(
            role_id=role_id,
            start=start,
            stop=stop,
            state=state,
            demand=demand, )

        db.session.add(schedule)
        db.session.commit()

        Schedules2Cache.delete(role.id)

        current_app.logger.info(
            "Schedule Created: start %s / org %s (%s) / location %s (%s) / role %s (%s)"
            % (start, org.id, org.name, loc.id, loc.name, role.id, role.name))
        return schedule

    @schedule_require_active
    def transition_to_chomp_queue(self):
        """ transition schedule state from unpublished to chomp queue """

        if self.state not in ["unpublished", "chomp-processing"]:
            raise Exception(
                "Schedule is in incorrect state for being added to chomp queue")

        self.state = "chomp-queue"
        db.session.commit()

        Schedules2Cache.delete(self.role_id)
        Shifts2Cache.delete(self.id)

        # logging
        current_app.logger.info("Schedule %s set to state %s" %
                                (self.id, self.state))

    @schedule_require_active
    def transition_to_chomp_processing(self):
        """ promote to processing in chomp """

        if self.state != "chomp-queue":
            raise Exception(
                "Schedule is in incorrect state for being promoted to chomp-processing"
            )

        self.state = "chomp-processing"
        self.chomp_start = datetime.utcnow()
        db.session.commit()

        Schedules2Cache.delete(self.role_id)
        Shifts2Cache.delete(self.id)

        # logging
        current_app.logger.info("Schedule %s set to state %s" %
                                (self.id, self.state))

    @schedule_require_active
    def transition_to_unpublished(self):
        """ transition state to unpublished """

        initial_state = self.state
        if initial_state not in ["initial", "chomp-processing"]:
            raise Exception(
                "Schedule is in incorrect state for being set to unpublished")

        if initial_state == "initial":
            current_app.logger.info("Creating fixed shifts for schedule %s" %
                                    self.id)

            # Find recurring shifts
            recurring_shifts = recurring_shift_model.RecurringShift.query.filter_by(
                role_id=self.role_id)

            # Create shifts for this week
            for recurring_shift in recurring_shifts:
                recurring_shift.create_shift2_for_schedule2(self.id)

        if initial_state == "chomp-processing":
            self.chomp_end = datetime.utcnow()

        self.state = "unpublished"
        db.session.commit()

        Schedules2Cache.delete(self.role_id)
        Shifts2Cache.delete(self.id)

        # logging
        current_app.logger.info("Schedule %s set to state %s" %
                                (self.id, self.state))

        if self.chomp_start and self.chomp_end:
            chomp_processing_time = (
                self.chomp_end - self.chomp_start).total_seconds()
            current_app.logger.info(
                "Schedule id %s Chomp calculation took %s seconds." %
                (self.id, chomp_processing_time))

        if initial_state == "chomp-processing":
            role = Role.query.get(self.role_id)
            loc = Location.query.get(role.location_id)
            org = organization_model.Organization.query.get(
                loc.organization_id)

            week_start = self.start.strftime("%Y-%m-%d")
            week = self.start.strftime("%b %-d")
            subject = "[Alert] Shift Scaffold Computed for %s - Week of %s in %s" % (
                role.name, week, loc.name)

            message = "The %s %s shift scaffold for the week of %s in %s has been finished:" % (
                org.name, role.name, week, loc.name)

            url = url_for('manager.manager_app', org_id=org.id, _external=True) \
                + "#locations/%s/scheduling/%s" % (loc.id, week_start)

            loc.send_manager_email(subject, message, url)

    @schedule_require_active
    def transition_to_mobius_queue(self):
        """ transition to queue for mobius processing """

        if self.state not in ["unpublished", "mobius-processing"]:
            raise Exception(
                "Schedule is in incorrect state for being added to mobius queue"
            )

        self.state = "mobius-queue"
        db.session.commit()

        Schedules2Cache.delete(self.role_id)
        Shifts2Cache.delete(self.id)

        # logging
        current_app.logger.info("Schedule %s set to state %s" %
                                (self.id, self.state))

    @schedule_require_active
    def transition_to_mobius_processing(self):
        """ transition to mobius processing """

        if self.state != "mobius-queue":
            raise Exception(
                "Schedule is in incorrect state for being promoted to mobius-processing"
            )

        self.state = "mobius-processing"
        self.mobius_start = datetime.utcnow()
        db.session.commit()

        Schedules2Cache.delete(self.role_id)
        Shifts2Cache.delete(self.id)

        # logging
        current_app.logger.info("Schedule %s set to state %s" %
                                (self.id, self.state))

    @schedule_require_active
    def transition_to_published(self):
        """ publish a schedule """

        if self.state not in ["unpublished", "mobius-processing"]:
            raise Exception(
                "Schedule is in incorrect state for being published")

        previous_state = self.state

        if self.state == "mobius-processing":
            self.mobius_end = datetime.utcnow()

        self.state = "published"
        db.session.commit()

        shifts_to_publish = shift2_model.Shift2.query \
            .filter(
                shift2_model.Shift2.role_id == self.role_id,
                shift2_model.Shift2.start >= self.start,
                shift2_model.Shift2.stop < self.stop
            ).all()

        for shift in shifts_to_publish:
            shift.published = True
            db.session.commit()

        Schedules2Cache.delete(self.role_id)
        Shifts2Cache.delete(self.id)

        # logging
        current_app.logger.info("Schedule %s set to state %s" %
                                (self.id, self.state))

        if self.mobius_start and self.mobius_end:
            mobius_processing_time = (
                self.mobius_end - self.mobius_start).total_seconds()
            current_app.logger.info(
                "Schedule id %s mobius calculation took %s seconds." %
                (self.id, mobius_processing_time))

        # prepare for email notifications
        role = Role.query.get(self.role_id)
        loc = Location.query.get(role.location_id)
        org = organization_model.Organization.query.get(loc.organization_id)

        week_start = self.start.strftime("%Y-%m-%d")
        week = self.start.strftime("%b %-d")
        subject = "Schedule published for %s - Week of %s in %s" % (
            role.name, week, loc.name)

        message = "The %s %s schedule for the week of %s in %s is now published:" % (
            org.name, role.name, week, loc.name)

        # only send manager emails if the schedule is automatically being
        # transitioned and its in the future
        if previous_state == "mobius-processing" and self.stop > datetime.utcnow(
        ):

            # Don't block emails if one fail
            url = url_for('manager.manager_app', org_id=org.id, _external=True) \
                + "#locations/%s/scheduling/%s" % (loc.id, week_start)

            loc.send_manager_email(subject, message, url)

        # users always get notified upon publishing
        workers = user_model.User.query \
            .join(RoleToUser) \
            .filter(
                RoleToUser.role_id == self.role_id,
                RoleToUser.archived == False
            ) \
            .all()

        # only send alerts for future schedules
        if self.stop > datetime.utcnow():
            for worker in workers:
                url = url_for('myschedules.myschedules_app', org_id=org.id, location_id=loc.id, role_id=self.role_id, user_id=worker.id, _external=True)\
                    + "#week/%s" % week_start

                try:
                    worker.send_email(subject,
                                      render_template(
                                          "email/notification-email.html",
                                          user=worker,
                                          message=message,
                                          url=url))

                except Exception as e:
                    current_app.logger.warning(
                        "Failed email send to manager in 'transition_to_published' - user id %s - email %s - %s"
                        % (worker.id, worker.email, e))
