import iso8601
from flask import g
from flask_restful import marshal, reqparse, Resource

from app.constants import MAX_SHIFT_LENGTH, SECONDS_PER_HOUR, API_ENVELOPE
from app.models import Shift2
from app.apiv2.decorators import verify_org_location_role, permission_location_manager
from app.apiv2.marshal import user_fields


class ShiftQueryApi(Resource):
    @verify_org_location_role
    @permission_location_manager
    def get(self, org_id, location_id, role_id):
        parser = reqparse.RequestParser()
        parser.add_argument("start", type=str, required=True)
        parser.add_argument("stop", type=str, required=True)
        parameters = parser.parse_args()

        allow_past = g.current_user.is_sudo(
        ) or g.current_user.is_org_admin_or_location_manager(org_id,
                                                             location_id)

        # start time
        try:
            start = iso8601.parse_date(parameters.get("start"))
        except iso8601.ParseError:
            return {
                "message": "Start time needs to be in ISO 8601 format"
            }, 400
        else:
            start = (start + start.utcoffset()).replace(tzinfo=None)

        # stop time
        try:
            stop = iso8601.parse_date(parameters.get("stop"))
        except iso8601.ParseError:
            return {"message": "Stop time needs to be in ISO 8601 format"}, 400
        else:
            stop = (stop + stop.utcoffset()).replace(tzinfo=None)

        # stop can't be before start
        if start >= stop:
            return {"message": "Stop time must be after start time"}, 400

        # shifts are limited to 23 hours in length
        if int((stop - start).total_seconds()) > MAX_SHIFT_LENGTH:
            return {
                "message":
                "Shifts cannot be more than %s hours long" %
                (MAX_SHIFT_LENGTH / SECONDS_PER_HOUR)
            }, 400

        # create a shift object - do NOT add to db session though
        shift = Shift2(role_id=role_id, start=start, stop=stop)

        within_caps, exceeds_caps = shift.get_all_eligible_users(
            allow_past=allow_past)
        marshal_within = [marshal(user, user_fields) for user in within_caps]
        marshal_exceeds = [marshal(user, user_fields) for user in exceeds_caps]

        for user in marshal_within:
            user["within_caps"] = True

        for user in marshal_exceeds:
            user["within_caps"] = False

        return {API_ENVELOPE: marshal_within + marshal_exceeds}
