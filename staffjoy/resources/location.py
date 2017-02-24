from staffjoy.resource import Resource
from staffjoy.resources.role import Role
from staffjoy.resources.manager import Manager
from staffjoy.resources.location_timeclock import LocationTimeclock
from staffjoy.resources.location_time_off_request import LocationTimeOffRequest
from staffjoy.resources.location_shift import LocationShift


class Location(Resource):
    PATH = "organizations/{organization_id}/locations/{location_id}"
    ID_NAME = "location_id"

    def get_roles(self, **kwargs):
        return Role.get_all(parent=self, **kwargs)

    def get_role(self, id):
        return Role.get(parent=self, id=id)

    def create_role(self, **kwargs):
        return Role.create(parent=self, **kwargs)

    def get_managers(self, **kwargs):
        return Manager.get_all(parent=self, **kwargs)

    def get_manager(self, id):
        return Manager.get(parent=self, id=id)

    def create_manager(self, **kwargs):
        """Typically just pass email"""
        return Manager.create(parent=self, **kwargs)

    def get_timeclocks(self, **kwargs):
        return LocationTimeclock.get_all(parent=self, **kwargs)

    def get_time_off_requests(self, **kwargs):
        return LocationTimeOffRequest.get_all(parent=self, **kwargs)

    def get_shifts(self, **kwargs):
        return LocationShift.get_all(parent=self, **kwargs)
