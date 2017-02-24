import datetime

import iso8601
from flask_restful import reqparse, marshal, Resource

from app.constants import API_ENVELOPE, NULL_TIME_OFF_REQUEST
from app.models import Organization, Location, Role, RoleToUser, TimeOffRequest
from app.helpers import normalize_to_midnight, get_default_tz
from app.apiv2.decorators import verify_org_location, \
    permission_location_manager
from app.apiv2.marshal import time_off_request_fields


class LocationTimeOffRequestsApi(Resource):
    @verify_org_location
    @permission_location_manager
    def get(self, org_id, location_id):
        """
        returns all time off request data that correlates a location
        """

        parser = reqparse.RequestParser()
        parser.add_argument("start", type=str)
        parser.add_argument("end", type=str)
        parser.add_argument("state", type=str)
        parameters = parser.parse_args()

        # Filter out null values
        parameters = dict((k, v) for k, v in parameters.iteritems()
                          if v is not None)

        org = Organization.query.get_or_404(org_id)
        location = Location.query.get_or_404(location_id)
        default_tz = get_default_tz()
        local_tz = location.timezone_pytz

        # prepare query
        time_off_requests = TimeOffRequest.query.join(RoleToUser).join(
            Role).join(Location).filter(Location.id == location_id)

        # start and end query
        # check for end 1st
        if "end" in parameters:

            if "start" not in parameters:
                return {
                    "message": "A start parameter must be given with an end."
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

            time_off_requests = time_off_requests.filter(
                TimeOffRequest.start < end)

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
                start = (start + start.utcoffset()).replace(tzinfo=default_tz)

        # otherwise determine when current week began
        else:
            now = local_tz.localize(datetime.datetime.utcnow())
            start = normalize_to_midnight(
                org.get_week_start_from_datetime(now)).astimezone(default_tz)

        # add start to query
        time_off_requests = time_off_requests.filter(
            TimeOffRequest.start >= start)

        if "state" in parameters:
            state = parameters.get("state")

            if (state == NULL_TIME_OFF_REQUEST):
                state = None

            time_off_requests = time_off_requests.filter(
                TimeOffRequest.state == state)

        return {
            API_ENVELOPE:
            map(lambda time_off_request: marshal(time_off_request, time_off_request_fields),
                time_off_requests.all())
        }
