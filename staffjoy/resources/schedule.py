from staffjoy.resource import Resource
from staffjoy.resources.preference import Preference
from staffjoy.resources.schedule_shift import ScheduleShift
from staffjoy.resources.schedule_timeclock import ScheduleTimeclock
from staffjoy.resources.schedule_time_off_request import ScheduleTimeOffRequest


class Schedule(Resource):
    PATH = "organizations/{organization_id}/locations/{location_id}/roles/{role_id}/schedules/{schedule_id}"
    ID_NAME = "schedule_id"

    def get_preferences(self, **kwargs):
        return Preference.get_all(parent=self, **kwargs)

    def get_preference(self, id):
        """ Get a worker's preference for a given week"""
        return Preference.get(parent=self, id=id)

    def create_preference(self, **kwargs):
        return Preference.create(parent=self, **kwargs)

    def get_schedule_shifts(self, **kwargs):
        return ScheduleShift.get_all(parent=self, **kwargs)

    def get_schedule_timeclocks(self, **kwargs):
        return ScheduleTimeclock.get_all(parent=self, **kwargs)

    def get_schedule_time_off_requests(self, **kwargs):
        return ScheduleTimeOffRequest.get_all(parent=self, **kwargs)
