from staffjoy.resource import Resource
from staffjoy.resources.timeclock import Timeclock
from staffjoy.resources.time_off_request import TimeOffRequest


class Worker(Resource):
    """Organization administrators"""
    PATH = "organizations/{organization_id}/locations/{location_id}/roles/{role_id}/users/{user_id}"
    ID_NAME = "user_id"

    def get_timeclocks(self, **kwargs):
        return Timeclock.get_all(parent=self, **kwargs)

    def get_timeclock(self, id):
        return Timeclock.get(parent=self, id=id)

    def create_timeclock(self, **kwargs):
        return Timeclock.create(parent=self, **kwargs)

    def get_time_off_requests(self, **kwargs):
        return TimeOffRequest.get_all(parent=self, **kwargs)

    def get_time_off_request(self, id):
        return TimeOffRequest.get(parent=self, id=id)

    def create_time_off_request(self, **kwargs):
        return TimeOffRequest.create(parent=self, **kwargs)
