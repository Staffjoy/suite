import json

from flask import g, current_app
from flask_restful import marshal, abort, reqparse, Resource

from app import db
from app.constants import API_ENVELOPE
from app.models import Schedule2, Organization
from app.caches import Schedules2Cache
from app.apiv2.decorators import verify_org_location_role_schedule, \
    permission_location_member, permission_location_manager
from app.apiv2.helpers import verify_days_of_week_struct
from app.apiv2.marshal import schedule_fields


class ScheduleApi(Resource):
    @verify_org_location_role_schedule
    @permission_location_member
    def get(self, org_id, location_id, role_id, schedule_id):

        response = {
            API_ENVELOPE: {},
            "resources":
            ["preferences", "shifts", "timeclocks", "timeoffrequests"],
        }

        schedule = Schedule2.query.get_or_404(schedule_id)
        schedule = marshal(schedule, schedule_fields)

        response[API_ENVELOPE] = schedule

        return response

    @verify_org_location_role_schedule
    @permission_location_manager
    def patch(self, org_id, location_id, role_id, schedule_id):
        schedule = Schedule2.query.get_or_404(schedule_id)
        org = Organization.query.get_or_404(org_id)

        parser = reqparse.RequestParser()
        parser.add_argument("demand", type=str)
        parser.add_argument("state", type=str)
        parser.add_argument("min_shift_length_hour", type=int)
        parser.add_argument("max_shift_length_hour", type=int)
        changes = parser.parse_args(strict=True)

        # Filter out null values
        changes = dict((k, v) for k, v in changes.iteritems() if v is not None)

        original_state = schedule.state

        if len(changes) == 0:
            return {"message": "No valid changes detected"}, 400

        # schedule can only be modified from initial or unpublished state if not sudo
        if not g.current_user.is_sudo():
            if original_state not in ["initial", "unpublished"]:
                return {
                    "message":
                    "You are not able to modify a schedule from its current state."
                }, 400

        if "min_shift_length_hour" in changes:
            min_shift_length_half_hour = changes["min_shift_length_hour"] * 2
        else:
            min_shift_length_half_hour = schedule.min_shift_length_half_hour

        if "max_shift_length_hour" in changes:
            max_shift_length_half_hour = changes["max_shift_length_hour"] * 2
        else:
            max_shift_length_half_hour = schedule.max_shift_length_half_hour

        # now verification
        # NOTE that if we choose to support lengths of 0, these 1st two checks will break
        # because None and 0 get evalulated as the same
        if bool(min_shift_length_half_hour) != bool(
                max_shift_length_half_hour):
            return {
                "message":
                "min_shift_length_hour and max_shift_length_hour most both be defined"
            }, 400

        if min_shift_length_half_hour and max_shift_length_half_hour:
            if min_shift_length_half_hour > max_shift_length_half_hour:
                return {
                    "message":
                    "min_shift_length_hour cannot be greater than max_shift_length_hour"
                }, 400

        if min_shift_length_half_hour:
            if not (1 <= min_shift_length_half_hour <= 46):
                return {
                    "message": "min_shift_length_hour must be between 1 and 24"
                }, 400

        if max_shift_length_half_hour:
            if not (1 <= max_shift_length_half_hour <= 46):
                return {
                    "message": "max_shift_length_hour must be between 1 and 24"
                }, 400

        if "min_shift_length_hour" in changes:
            del changes["min_shift_length_hour"]
            changes["min_shift_length_half_hour"] = min_shift_length_half_hour

        if "max_shift_length_hour" in changes:
            del changes["max_shift_length_hour"]
            changes["max_shift_length_half_hour"] = max_shift_length_half_hour

        if "demand" in changes:

            # admins can only modify demand in the unpublished state
            if not g.current_user.is_sudo():
                if changes.get("state", schedule.state) not in [
                        "unpublished", "chomp-queue"
                ]:
                    return {
                        "message":
                        "Admins can only modify demand when the schedule is in the unpublished state."
                    }, 400

            # demand can be set to None when it is sent down without a value in the request
            # (not "") will resolve to True, which we consider None - assume json for all other cases
            if not changes["demand"]:
                changes["demand"] = None
            else:
                try:
                    demand = json.loads(changes.get("demand"))
                except:
                    return {"message": "Unable to parse demand json body"}, 400

                if demand is None or not isinstance(demand, dict):
                    return {"message": "Unable to parse demand json body"}, 400

                # Check that days of week are right
                if not verify_days_of_week_struct(demand):
                    return {"message": "demand is improperly formatted"}, 400

                try:
                    changes["demand"] = json.dumps(demand)
                except Exception as exception:
                    return {"message": "Unable to parse demand json body"}, 400

            g.current_user.track_event("updated_demand")

        if "state" in changes:
            state = changes.get("state")

            if state == original_state:
                return {
                    "message": "Schedule is already in state %s." % state
                }, 400

            if state not in [
                    "unpublished", "chomp-queue", "mobius-queue", "published"
            ]:
                return {
                    "message":
                    "State can only be updated to 'unpublished', 'chomp-queue', 'mobius-queue' or 'done'."
                }, 400

            if not org.active:
                return {
                    "message":
                    "This organization must be active for a state change"
                }, 400

            if state == "chomp-queue":
                if not changes.get("min_shift_length_half_hour",
                                   schedule.min_shift_length_half_hour):
                    return {
                        "message":
                        "min_shift_length_hour must be set for chomp queue"
                    }, 400

                if not changes.get("max_shift_length_half_hour",
                                   schedule.max_shift_length_half_hour):
                    return {
                        "message":
                        "max_shift_length_hour must be set for chomp queue"
                    }, 400

                if original_state not in ["unpublished", "chomp-processing"]:
                    return {"message": "This state change is not allowed"}, 400

                # reset timing measurements - although they will soon be reset, the monitoring timing
                # may be inaccurate for the duration of calculation (e.g. a requeue)
                changes["chomp_start"] = None
                changes["chomp_end"] = None

                if not g.current_user.is_sudo():
                    g.current_user.track_event("chomp_schedule_calculation")

                schedule.transition_to_chomp_queue()

            elif state == "published":

                if original_state not in ["unpublished", "mobius-processing"]:
                    return {"message": "This state change is not allowed"}, 400

                schedule.transition_to_published()

                if not g.current_user.is_sudo():
                    g.current_user.track_event("published_schedule")

            elif state == "mobius-queue":

                if original_state not in ["unpublished", "mobius-processing"]:
                    return {"message": "This state change is not allowed"}, 400

                # reset timing measurements - although they will soon be reset, the monitoring timing
                # may be inaccurate for the duration of calculation (e.g. a requeue)
                changes["mobius_start"] = None
                changes["mobius_end"] = None

                schedule.transition_to_mobius_queue()

            elif state == "unpublished":
                if original_state not in ["initial", "chomp-processing"]:
                    return {
                        "message":
                        "Schedule cannot be set to unpublished from its current state"
                    }

                schedule.transition_to_unpublished()

        for change, value in changes.iteritems():
            try:
                setattr(schedule, change, value)
                db.session.commit()
            except Exception as exception:
                db.session.rollback()
                current_app.logger.exception(str(exception))
                abort(400)

        Schedules2Cache.delete(role_id)

        return changes
