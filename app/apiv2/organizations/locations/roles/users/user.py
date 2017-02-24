from flask import g, current_app
from flask_restful import marshal, abort, reqparse, inputs, Resource
import json
import datetime

from app import db
from app.constants import API_ENVELOPE
from app.models import User, Organization, Location, Role, RoleToUser, \
    Schedule2, Shift2, TimeOffRequest, RecurringShift, Timeclock
from app.caches import Shifts2Cache
from app.apiv2.decorators import verify_org_location_role_user, \
    permission_location_manager, permission_location_manager_or_self
from app.apiv2.marshal import user_fields, role_to_user_fields
from app.apiv2.email import alert_email, alert_timeclock_change
from app.apiv2.helpers import verify_days_of_week_struct


class RoleMemberApi(Resource):
    @verify_org_location_role_user
    @permission_location_manager
    def delete(self, org_id, location_id, role_id, user_id):
        user = User.query.get_or_404(user_id)
        role = Role.query.get_or_404(role_id)

        assoc = RoleToUser.query.filter_by(
            user_id=user.id, role_id=role.id).first()
        if assoc is None:
            abort(404)

        if assoc.archived:
            abort(400)

        assoc.archived = True

        try:
            db.session.commit()
        except:
            abort(500)

        location = Location.query.get(location_id)
        organization = Organization.query.get(org_id)

        # Set future shifts to unassigned
        # Be careful to not unassign them from other orgs!
        future_shifts = Shift2.query.filter(
            Shift2.user_id == user.id,
            Shift2.role_id == role_id,
            Shift2.start > datetime.datetime.utcnow(), ).all()

        for shift in future_shifts:
            shift.user_id = None

            # clear cache too
            schedule = Schedule2.query \
                .filter(
                    Schedule2.role_id == role_id,
                    Schedule2.start <= shift.start,
                    Schedule2.stop > shift.start,
                ).first()

            if schedule is not None:
                Shifts2Cache.delete(schedule.id)

        # deny future time off requests that are open
        future_time_off_requests = TimeOffRequest.query \
            .filter_by(role_to_user_id=assoc.id) \
            .filter_by(state=None) \
            .filter(
                TimeOffRequest.start > datetime.datetime.utcnow(),
            ) \
            .all()

        for time_off_request in future_time_off_requests:
            time_off_request.state = "denied"

        # unassign all recurring shifts
        recurring_shifts = RecurringShift.query \
            .filter_by(
                role_id=role_id,
                user_id=user_id
            ) \
            .all()

        for recurring_shift in recurring_shifts:
            current_app.logger.info(
                "Setting recurring shift %s to unassigned because user %s is being removed from role %s"
                % (recurring_shift.id, user_id, role_id))
            recurring_shift.user_id = None

        # close open timeclocks
        timeclocks = Timeclock.query \
            .filter_by(
                role_id=role_id,
                user_id=user_id,
                stop=None
            ) \
            .all()

        for timeclock in timeclocks:
            original_start = timeclock.start
            original_stop = timeclock.stop

            timeclock.stop = datetime.datetime.utcnow()
            current_app.logger.info(
                "Closing timeclock %s because user %s is being removed from role %s"
                % (timeclock.id, user_id, role_id))

            alert_timeclock_change(timeclock, org_id, location_id, role_id,
                                   original_start, original_stop, user,
                                   g.current_user)

        alert_email(
            user,
            "You have been removed from a team at %s" % organization.name,
            "You have been removed from the team <b>%s</b> at the <b>%s</b> location of <b>%s</b>. This may happen as the scheduling manager changes your role or location."
            % (role.name, location.name, organization.name),
            force_send=True)
        g.current_user.track_event("deleted_role_member")
        return {}, 204

    @verify_org_location_role_user
    @permission_location_manager_or_self
    def get(self, org_id, location_id, role_id, user_id):
        user = User.query.get_or_404(user_id)
        rtu = RoleToUser.query.filter_by(
            user_id=user_id, role_id=role_id).first()

        if user is None:
            abort(404)

        if rtu is None:
            abort(404)

        data = {}
        data.update(marshal(user, user_fields))
        data.update(marshal(rtu, role_to_user_fields))

        return {
            API_ENVELOPE: data,
            "resources": ["timeclocks", "timeoffrequests"],
        }

    @verify_org_location_role_user
    @permission_location_manager
    def patch(self, org_id, location_id, role_id, user_id):
        parser = reqparse.RequestParser()
        parser.add_argument("min_hours_per_workweek", type=int)
        parser.add_argument("max_hours_per_workweek", type=int)
        parser.add_argument("internal_id", type=str)
        parser.add_argument("archived", type=inputs.boolean)
        parser.add_argument("activateReminder", type=inputs.boolean)
        parser.add_argument("working_hours", type=str)

        # Filter out null values
        changes = parser.parse_args(strict=True)
        changes = dict((k, v) for k, v in changes.iteritems() if v is not None)

        rtu = RoleToUser.query.filter_by(
            user_id=user_id, role_id=role_id).first()
        if rtu is None:
            abort(404)

        if "archived" in changes:
            if not g.current_user.is_sudo():
                return {
                    "message":
                    "You do not have permission to modify 'archived'."
                }, 401

            role = Role.query.get_or_404(role_id)
            if role.archived:
                return {"message": "The parent role is archived."}, 400

        elif rtu.archived:
            abort(400)

        # activation email reminder - it can't be committed to this RTU model though
        if "activateReminder" in changes:
            user = User.query.get_or_404(user_id)
            org = Organization.query.get_or_404(org_id)

            if user.active:
                return {"message": "This user is already active"}, 400

            user.send_activation_reminder(user, org.name)
            del changes["activateReminder"]

        # extract workweek limits and convert into half hour
        if "min_hours_per_workweek" in changes:
            min_half_hours_per_workweek = changes["min_hours_per_workweek"] * 2
        else:
            min_half_hours_per_workweek = rtu.min_half_hours_per_workweek

        if "max_hours_per_workweek" in changes:
            max_half_hours_per_workweek = changes["max_hours_per_workweek"] * 2
        else:
            max_half_hours_per_workweek = rtu.max_half_hours_per_workweek

        # some verification
        if min_half_hours_per_workweek > max_half_hours_per_workweek:
            return {
                "message":
                "min_hours_per_workweek cannot be greater than max_hours_per_workweek"
            }, 400

        if not (0 <= min_half_hours_per_workweek <= 336):
            return {
                "message": "min_hours_per_workweek cannot be less than 0"
            }, 400

        if not (0 <= max_half_hours_per_workweek <= 336):
            return {
                "message": "max_hours_per_workweek cannot be greater than 168"
            }, 400

        # the proper db term must be submitted if it is intended to be changed
        if "min_hours_per_workweek" in changes:
            del changes["min_hours_per_workweek"]
            changes[
                "min_half_hours_per_workweek"] = min_half_hours_per_workweek

        if "max_hours_per_workweek" in changes:
            del changes["max_hours_per_workweek"]
            changes[
                "max_half_hours_per_workweek"] = max_half_hours_per_workweek

        if changes.get("working_hours") is not None:
            try:
                working_hours = json.loads(changes.get("working_hours"))
            except:
                return {
                    "message": "Unable to parse working hours json body"
                }, 400
            if working_hours is None:
                return {
                    "message": "Unable to parse working hours json body"
                }, 400
            if not verify_days_of_week_struct(working_hours, True):
                return {
                    "message": "working hours is improperly formatted"
                }, 400

            g.current_user.track_event("modified_working_hours")

        for change, value in changes.iteritems():
            if value is not None:
                try:
                    setattr(rtu, change, value)
                    db.session.add(rtu)
                    db.session.commit()
                except Exception as exception:
                    db.session.rollback()
                    current_app.logger.exception(str(exception))
                    abort(400)

        g.current_user.track_event("modified_role_member")
        return changes
