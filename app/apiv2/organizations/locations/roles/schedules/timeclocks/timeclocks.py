from flask_restful import marshal, reqparse, Resource

from app.constants import API_ENVELOPE
from app.models import Schedule2, Timeclock

from app.apiv2.decorators import verify_org_location_role_schedule, \
    permission_location_manager
from app.apiv2.marshal import timeclock_fields


class ScheduleTimeclocksApi(Resource):
    @verify_org_location_role_schedule
    @permission_location_manager
    def get(self, org_id, location_id, role_id, schedule_id):
        """
        returns all timeclock data that correlates to the timespan of a given schedule
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
        timeclocks = Timeclock.query \
            .filter_by(role_id=role_id) \
            .filter(Timeclock.start >= schedule.start) \
            .filter(Timeclock.start < schedule.stop)

        # add user id if optionally added
        if "user_id" in parameters:
            timeclocks = timeclocks.filter_by(
                user_id=parameters.get("user_id"))

        return {
            API_ENVELOPE:
            map(lambda timeclock: marshal(timeclock, timeclock_fields),
                timeclocks.all())
        }
