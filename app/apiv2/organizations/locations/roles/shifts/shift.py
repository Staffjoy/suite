from copy import deepcopy

import iso8601
from flask import g, current_app
from flask_restful import marshal, abort, reqparse, Resource, inputs

from app import db, constants
from app.helpers import get_default_tz
from app.models import Organization, Location, RoleToUser, Shift2, Schedule2
from app.caches import Shifts2Cache
from app.apiv2.decorators import verify_org_location_role_shift, \
    permission_location_manager, permission_location_member
from app.apiv2.marshal import shift_fields
from app.apiv2.email import alert_changed_shift, alert_available_shifts


class ShiftApi(Resource):
    @verify_org_location_role_shift
    @permission_location_member
    def get(self, org_id, location_id, role_id, shift_id):
        shift = Shift2.query.get_or_404(shift_id)
        return {
            constants.API_ENVELOPE: marshal(shift, shift_fields),
            "resources": ["users"],
        }

    @verify_org_location_role_shift
    @permission_location_member
    def patch(self, org_id, location_id, role_id, shift_id):

        parser = reqparse.RequestParser()
        parser.add_argument("start", type=str)
        parser.add_argument("stop", type=str)
        parser.add_argument("user_id", type=int)
        parser.add_argument("published", type=inputs.boolean)
        parser.add_argument("description", type=str)
        changes = parser.parse_args(strict=True)

        # Filter out null values
        changes = dict((k, v) for k, v in changes.iteritems() if v is not None)

        shift = Shift2.query.get(shift_id)
        shift_copy = deepcopy(shift)
        org = Organization.query.get(org_id)
        location = Location.query.get(location_id)
        role_to_user = None
        default_tz = get_default_tz()
        local_tz = location.timezone_pytz

        user_id = changes.get("user_id", shift.user_id)
        if user_id != shift.user_id:
            # Need this for later
            old_user_id = shift.user_id
        else:
            old_user_id = None

        # Check if user is in that role
        if user_id is not None and user_id != 0:
            role_to_user = RoleToUser.query.filter_by(
                user_id=user_id,
                role_id=role_id, ).first_or_404()

        # People that are not Sudo or Org Admins cannot do anything
        # except claim a shift.
        # (But a worker that's also, say, sudo can do so!)
        if not (g.current_user.is_sudo() or
                g.current_user.is_org_admin_or_location_manager(org_id,
                                                                location_id)):
            # User claiming a shift!

            # Check that it's the only change being made
            if set(("user_id", )) != set(changes):
                return {
                    "message":
                    "You are only allowed to claim unassigned shifts"
                }, 400

            # this user must be active to claim
            if role_to_user:
                if role_to_user.archived:
                    abort(404)

            # This user can only claim shifts for themself
            if user_id != g.current_user.id:
                return {
                    "message":
                    "You are not permitted to assign a shift to somebody else"
                }, 400

            # And the shift must be currently unclaimed
            if shift.user_id != 0 and shift.user_id is not None:
                return {"message": "Shift already claimed"}, 400

            # the shift cannot be in the past
            if shift.is_in_past:
                return {"message": "Shift is in the past"}, 400

            # And the user cannot claim the shift if it overlaps
            shift_copy.user_id = user_id
            if shift_copy.has_overlaps():
                return {
                    "message": "Shift overlaps with an existing shift"
                }, 400

            # Users on boss cannot claim if it violates caps and org doesn't allow exceeding
            if (org.is_plan_boss() and
                    not org.workers_can_claim_shifts_in_excess_of_max and
                    not shift_copy.is_within_caps(user_id)):
                return {"message": "This shift breaks existing limits"}, 400

            current_app.logger.info("User %s is claiming shift %s" %
                                    (user_id, shift.id))

        # admin or sudo only

        # get start and stop values
        if "start" in changes:
            try:
                start = iso8601.parse_date(changes.get("start"))
            except iso8601.ParseError:
                return {
                    "message": "Start time needs to be in ISO 8601 format"
                }, 400
            else:
                start = (start + start.utcoffset()).replace(tzinfo=default_tz)
        else:
            start = shift.start.replace(tzinfo=default_tz)

        # get new or current stop value
        if "stop" in changes:
            try:
                stop = iso8601.parse_date(changes.get("stop"))
            except iso8601.ParseError:
                return {
                    "message": "Stop time needs to be in ISO 8601 format"
                }, 400
            else:
                stop = (stop + stop.utcoffset()).replace(tzinfo=default_tz)
        else:
            stop = shift.stop.replace(tzinfo=default_tz)

        # stop can't be before start
        if start >= stop:
            return {"message": "Stop time must be after start time"}, 400

        # shifts are limited to 23 hours in length
        if int((stop - start).total_seconds()) > constants.MAX_SHIFT_LENGTH:
            return {
                "message":
                "Shifts cannot be more than %s hours long" %
                (constants.MAX_SHIFT_LENGTH / constants.SECONDS_PER_HOUR)
            }, 400

        # Unassigned shifts need to be converted to None in db
        if user_id == 0:
            user_id = None
            changes["user_id"] = None

        # assume always checking for overlap except for 3 cases
        # 1) shift was and still will be unassigned
        # 2) shift is becoming unassigned
        # 3) only published state is being changed
        overlap_check = True

        # shift was, and still is unassigned
        if shift.user_id is None and "user_id" not in changes:
            overlap_check = False

        # shift is becoming unassigned, don't need to check
        if "user_id" in changes and (user_id is None or user_id == 0):
            overlap_check = False

        # only published being modified, don't care
        if set(("published", )) == set(changes):
            overlap_check = False

        # a person cannot have overlapping shifts
        if overlap_check:

            shift_copy.start = start.replace(tzinfo=None)
            shift_copy.stop = stop.replace(tzinfo=None)
            shift_copy.user_id = user_id

            # check for overlap - don't need to check for in past here
            if shift_copy.has_overlaps():
                return {
                    "message": "Shift overlaps with an existing shift"
                }, 400

        # start/stop need to be in isoformat for committing changes
        if "start" in changes:
            changes["start"] = start.isoformat()

        if "stop" in changes:
            changes["stop"] = stop.isoformat()

        if "description" in changes:
            if len(changes["description"]) > Shift2.MAX_DESCRIPTION_LENGTH:
                return {
                    "message":
                    "Description cannot me more than %s characters" %
                    Shift2.MAX_DESCRIPTION_LENGTH
                }, 400

        for change, value in changes.iteritems():
            try:
                setattr(shift, change, value)
                db.session.commit()
            except Exception as exception:
                db.session.rollback()
                current_app.logger.exception(str(exception))
                abort(400)

        g.current_user.track_event("modified_shift")

        # check if a schedule exists during this time - if so, bust the cache
        schedule = Schedule2.query \
            .filter(
                Schedule2.role_id == role_id,
                Schedule2.start <= shift.start,
                Schedule2.stop > shift.start,
            ).first()

        if schedule is not None:
            Shifts2Cache.delete(schedule.id)

        if shift.published and not shift.is_in_past:
            local_datetime = default_tz.localize(
                shift.start).astimezone(local_tz)

            # if shift became unassigned, send an email to notify workers
            if shift.user_id is None:

                # get all users who are eligible for the shift
                eligible_users = shift.get_users_within_caps()

                alert_available_shifts(
                    org_id,
                    location_id,
                    role_id,
                    local_datetime,
                    eligible_users,
                    exclude_id=old_user_id)

            if old_user_id != shift.user_id:

                # old worker
                if g.current_user.id != old_user_id:
                    alert_changed_shift(org_id, location_id, role_id,
                                        local_datetime, old_user_id)

                # new worker
                if g.current_user.id != shift.user_id:
                    alert_changed_shift(
                        org_id,
                        location_id,
                        role_id,
                        local_datetime,
                        shift.user_id, )

        return changes

    @verify_org_location_role_shift
    @permission_location_manager
    def delete(self, org_id, location_id, role_id, shift_id):
        shift = Shift2.query.get_or_404(shift_id)
        location = Location.query.get_or_404(location_id)
        user_id = shift.user_id  # cached becuase we are deleting the shift

        # check if a schedule exists during this time - if so, bust the cache
        schedule = Schedule2.query \
            .filter(
                Schedule2.role_id == role_id,
                Schedule2.start <= shift.start,
                Schedule2.stop > shift.start,
            ).first()

        try:
            db.session.delete(shift)
            db.session.commit()
        except Exception as exception:
            db.session.rollback()
            current_app.logger.error(str(exception))
            abort(400)

        # clear cache
        if schedule is not None:
            Shifts2Cache.delete(schedule.id)

        if (g.current_user.id != shift.user_id) and shift.published:
            default_tz = get_default_tz()
            local_tz = location.timezone_pytz
            local_datetime = default_tz.localize(
                shift.start).astimezone(local_tz)
            alert_changed_shift(org_id, location_id, role_id, local_datetime,
                                user_id)

        g.current_user.track_event("deleted_shift")
        return {}, 204
