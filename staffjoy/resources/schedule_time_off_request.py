from staffjoy.resource import Resource


class ScheduleTimeOffRequest(Resource):
    """this is only a get collection endpoint"""
    PATH = "organizations/{organization_id}/locations/{location_id}/roles/{role_id}/schedules/{schedule_id}/timeoffrequests/"
