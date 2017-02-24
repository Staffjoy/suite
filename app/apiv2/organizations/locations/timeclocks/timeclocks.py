import datetime

import iso8601
from flask_restful import reqparse, marshal, Resource, inputs

from app.constants import API_ENVELOPE
from app.models import Organization, Location, Role, Timeclock, User
from app.helpers import normalize_to_midnight, get_default_tz
from app.apiv2.decorators import verify_org_location, \
    permission_location_manager
from app.apiv2.marshal import timeclock_fields


class LocationTimeclocksApi(Resource):
    @verify_org_location
    @permission_location_manager
    def get(self, org_id, location_id):
        """
        returns all timeclock data that correlates to a location
        """

        parser = reqparse.RequestParser()
        parser.add_argument("active", type=inputs.boolean)
        parser.add_argument("start", type=str)
        parser.add_argument("end", type=str)
        parameters = parser.parse_args()

        # Filter out null values
        parameters = dict((k, v) for k, v in parameters.iteritems()
                          if v is not None)

        org = Organization.query.get_or_404(org_id)
        location = Location.query.get_or_404(location_id)
        default_tz = get_default_tz()
        local_tz = location.timezone_pytz

        timeclocks = Timeclock.query.join(User).join(Role).join(
            Location).filter(Location.id == location_id)

        # if searching for active timeclocks, do not include start and end query ranges
        if "active" in parameters:
            if "start" in parameters or "end" in parameters:
                return {
                    "message": "Cannot have start or end with active parameter"
                }, 400

            timeclocks = timeclocks.filter(Timeclock.stop == None)

        # start and end query
        else:

            # check for end 1st
            if "end" in parameters:

                if "start" not in parameters:
                    return {
                        "message":
                        "A start parameter must be given with an end."
                    }, 400

                # ensure good iso formatting
                try:
                    end = iso8601.parse_date(parameters.get("end"))
                except iso8601.ParseError:
                    return {
                        "message":
                        "End time parameter time needs to be in ISO 8601 format"
                    }, 400
                else:
                    end = (end + end.utcoffset()).replace(tzinfo=default_tz)

                timeclocks = timeclocks.filter(Timeclock.start < end)

            # if a start is defined, it must be iso 8601
            if "start" in parameters:

                # make sure start is in right format, and also convert to full iso form
                try:
                    start = iso8601.parse_date(parameters.get("start"))
                except iso8601.ParseError:
                    return {
                        "message":
                        "Start time parameter needs to be in ISO 8601 format"
                    }, 400
                else:
                    start = (start + start.utcoffset()).replace(
                        tzinfo=default_tz)

            # otherwise determine when current week began
            else:
                now = local_tz.localize(datetime.datetime.utcnow())
                start = normalize_to_midnight(
                    org.get_week_start_from_datetime(now)).astimezone(
                        default_tz)

            # add start to query
            timeclocks = timeclocks.filter(Timeclock.start >= start)

        return {
            API_ENVELOPE:
            map(lambda timeclock: marshal(timeclock, timeclock_fields),
                timeclocks.all())
        }
