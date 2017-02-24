from staffjoy.resource import Resource
from staffjoy.resources.worker import Worker
from staffjoy.resources.schedule import Schedule
from staffjoy.resources.shift import Shift
from staffjoy.resources.shift_query import ShiftQuery
from staffjoy.resources.recurring_shift import RecurringShift


class Role(Resource):
    PATH = "organizations/{organization_id}/locations/{location_id}/roles/{role_id}"
    ID_NAME = "role_id"

    def get_workers(self, **kwargs):
        return Worker.get_all(parent=self, **kwargs)

    def get_worker(self, id=id):
        return Worker.get(parent=self, id=id)

    def create_worker(self, **kwargs):
        return Worker.create(parent=self, **kwargs)

    def get_schedules(self, **kwargs):
        return Schedule.get_all(parent=self, **kwargs)

    def get_schedule(self, id):
        return Schedule.get(parent=self, id=id)

    def get_shifts(self, **kwargs):
        return Shift.get_all(parent=self, **kwargs)

    def get_shift(self, id):
        return Shift.get(parent=self, id=id)

    def get_shift_query(self, **kwargs):
        return ShiftQuery.get_all(parent=self, **kwargs)

    def create_shift(self, **kwargs):
        return Shift.create(parent=self, **kwargs)

    def get_recurring_shifts(self, **kwargs):
        return RecurringShift.get_all(parent=self, **kwargs)

    def get_recurring_shift(self, id):
        return RecurringShift.get(parent=self, id=id)

    def create_recurring_shift(self, **kwargs):
        return RecurringShift.create(parent=self, **kwargs)
