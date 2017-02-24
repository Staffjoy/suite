import datetime
import iso8601

from flask import g
from flask_restful import marshal, reqparse, Resource, inputs
from sqlalchemy import asc

from copy import deepcopy

from app.constants import API_ENVELOPE
from app.models import Organization, RoleToUser, Schedule2, Shift2
from app.caches import Shifts2Cache
from app.apiv2.decorators import verify_org_location_role_schedule, \
    permission_location_member
from app.apiv2.marshal import shift_fields


class ScheduleShiftsApi(Resource):
    @verify_org_location_role_schedule
    @permission_location_member
    def get(self, org_id, location_id, role_id, schedule_id):
        """
        gets data for this schedule - via caching!
        """

        parser = reqparse.RequestParser()
        parser.add_argument(
            "include_summary", type=inputs.boolean, default=False)
        parser.add_argument(
            "filter_by_published", type=inputs.boolean, default=False)
        parser.add_argument("claimable_by_user", type=int)
        parameters = parser.parse_args()

        # Filter out null values
        parameters = dict((k, v) for k, v in parameters.iteritems()
                          if v is not None)

        # claimable_by_user must be the only parameter
        if (parameters.get("claimable_by_user") and
            (parameters.get("include_summary") or
             parameters.get("filter_by_published"))):
            return {
                "message":
                "Cannot return claimable shifts and summary or published shifts in the same query"
            }, 400

        org = Organization.query.get(org_id)
        schedule = Schedule2.query.get_or_404(schedule_id)
        shifts = Shifts2Cache.get(schedule_id)

        if shifts is None:
            shifts = Shift2.query \
                .filter(
                    Shift2.role_id == role_id,
                    Shift2.stop >= schedule.start,
                    Shift2.start < schedule.stop,
                ) \
                .order_by(asc(Shift2.start)) \
                .all()

            shifts = map(lambda shift: marshal(shift, shift_fields), shifts)

            Shifts2Cache.set(schedule_id, shifts)

        # Filter shifts by ones a user can claim
        if "claimable_by_user" in parameters and parameters.get(
                "claimable_by_user") > 0:
            # 1) Check if user in role
            role_to_user = RoleToUser.query\
                .filter_by(
                    user_id=parameters["claimable_by_user"],
                    role_id=role_id, archived=False)\
                .first()
            if role_to_user is None:
                return {"message": "user is not in the role"}, 400

            # 2) reduce shifts to unassigned ones that don't overlap with user in question
            if g.current_user.is_sudo(
            ) or g.current_user.is_org_admin_or_location_manager(org_id,
                                                                 location_id):
                allow_past = True
            else:
                allow_past = False

            shifts = self._filter_overlapping_shifts(
                shifts,
                role_id,
                parameters["claimable_by_user"],
                allow_past=allow_past, )

            # 3) If org does not allow claiming in excess of caps, filter by hourly caps
            if org.is_plan_boss(
            ) and not org.workers_can_claim_shifts_in_excess_of_max:
                shifts = self._filter_allowed_shifts(
                    shifts, role_id, parameters["claimable_by_user"], schedule)

        if parameters.get("filter_by_published"):
            shifts = filter(lambda shift: shift.get("published") == True,
                            shifts)

        result = {
            API_ENVELOPE: shifts,
        }

        if parameters.get("include_summary"):
            users_summary = {}

            for shift in shifts:
                user_id = shift.get("user_id")
                duration = int((
                    iso8601.parse_date(shift.get("stop")) - iso8601.parse_date(
                        shift.get("start"))).total_seconds() / 60)

                if user_id in users_summary.keys():
                    users_summary[user_id]["shifts"] += 1
                    users_summary[user_id]["minutes"] += duration
                else:
                    if user_id > 0:
                        name = shift.get("user_name")
                    else:
                        name = "Unassigned shifts"

                    users_summary[user_id] = {
                        "user_id": user_id,
                        "user_name": name,
                        "shifts": 1,
                        "minutes": duration,
                    }

            result["summary"] = users_summary.values()

        return result

    def _filter_overlapping_shifts(self,
                                   available_shifts,
                                   role_id,
                                   user_id,
                                   allow_past=False):
        """
        Return shifts that do not overlap with existing user shifts
        Given available shifts and existing user shifts for a given schedule.
        Also filter past shifts

        available_shifts must come from cache or be marshalled 1st
        """

        filtered_shifts = []

        for shift in available_shifts:
            start = iso8601.parse_date(shift.get("start")).replace(tzinfo=None)

            # check if shift in past
            if not allow_past and (datetime.datetime.utcnow() > start):
                continue

            # shift must be published
            if not shift["published"]:
                continue

            # Check whether the shift is unassigned
            if shift["user_id"] > 0:
                continue

            shift_model_copy = deepcopy(Shift2.query.get(shift["id"]))
            shift_model_copy.user_id = user_id
            if shift_model_copy.has_overlaps():
                continue

            filtered_shifts.append(shift)

        return filtered_shifts

    def _filter_allowed_shifts(self, shifts, role_id, user_id, schedule):
        """
        filters a list of shifts to only those that would not exceed the user's caps
        needs filter_overlapping_shifts to be run 1st
        """

        filtered_shifts = []

        for shift in shifts:
            shift_model = Shift2.query.get(shift["id"])

            if shift_model.is_within_caps(user_id):
                filtered_shifts.append(shift)

        return filtered_shifts
