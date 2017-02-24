from flask_restful import marshal, reqparse, Resource

from app.constants import API_ENVELOPE
from app.models import Schedule2, TimeOffRequest, RoleToUser

from app.apiv2.decorators import verify_org_location_role_schedule, \
    permission_location_manager
from app.apiv2.marshal import time_off_request_fields


class ScheduleTimeOffRequestsApi(Resource):
    @verify_org_location_role_schedule
    @permission_location_manager
    def get(self, org_id, location_id, role_id, schedule_id):
        """
        returns all time off request data that correlates to the timespan of a given schedule
        """

        parser = reqparse.RequestParser()
        parser.add_argument("user_id", type=int)
        parameters = parser.parse_args()

        # Filter out null values
        parameters = dict((k, v) for k, v in parameters.iteritems()
                          if v is not None)

        # get schedule object
        schedule = Schedule2.query.get_or_404(schedule_id)

        # prepare query
        time_off_requests = TimeOffRequest.query \
            .join(RoleToUser) \
            .filter(
                RoleToUser.role_id == role_id,
                TimeOffRequest.start >= schedule.start,
                TimeOffRequest.start < schedule.stop
            )

        # add user id if optionally added
        if "user_id" in parameters:
            time_off_requests = time_off_requests\
                .filter(
                   RoleToUser.user_id == parameters.get("user_id")
                )

        return {
            API_ENVELOPE:
            map(lambda time_off_request: marshal(time_off_request, time_off_request_fields),
                time_off_requests.all())
        }
