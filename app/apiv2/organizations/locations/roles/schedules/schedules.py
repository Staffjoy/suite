import iso8601
from flask_restful import marshal, reqparse, Resource

from app.helpers import get_default_tz
from app.constants import API_ENVELOPE
from app.models import Schedule2
from app.caches import Schedules2Cache
from app.apiv2.decorators import verify_org_location_role,\
    permission_location_member
from app.apiv2.marshal import schedule_fields


class SchedulesApi(Resource):
    @verify_org_location_role
    @permission_location_member
    def get(self, org_id, location_id, role_id):

        parser = reqparse.RequestParser()
        parser.add_argument("start", type=str)
        parser.add_argument("end", type=str)
        parameters = parser.parse_args(strict=True)

        # Filter out null values
        parameters = dict((k, v) for k, v in parameters.iteritems()
                          if v is not None)

        response = {
            API_ENVELOPE: [],
        }

        schedules = Schedules2Cache.get(role_id)

        if schedules is None:
            schedules = Schedule2.query \
                .filter_by(role_id=role_id) \
                .order_by(
                    Schedule2.start.asc(),
                ) \
                .all()

            schedules = map(
                lambda schedule: marshal(schedule, schedule_fields), schedules)
            Schedules2Cache.set(role_id, schedules)

        default_tz = get_default_tz()

        if "start" in parameters:
            try:
                start = iso8601.parse_date(parameters.get("start"))
            except iso8601.ParseError:
                return {
                    "message":
                    "Start time parameter needs to be in ISO 8601 format"
                }, 400
            else:
                start = (start + start.utcoffset()).replace(tzinfo=default_tz)

            # run a filter to only keep schedules that occur after start
            schedules = filter(
                lambda x: \
                    iso8601.parse_date(x.get("start")).replace(tzinfo=default_tz) >= start,
                    schedules
                )

        if "end" in parameters:
            try:
                end = iso8601.parse_date(parameters.get("end"))
            except iso8601.ParseError:
                return {
                    "message":
                    "End time parameter time needs to be in ISO 8601 format"
                }, 400
            else:
                end = (end + end.utcoffset()).replace(tzinfo=default_tz)

            schedules = filter(
                lambda x: \
                    iso8601.parse_date(x.get("start")).replace(tzinfo=default_tz) < end,
                    schedules
                )

        response["data"] = schedules
        return response
