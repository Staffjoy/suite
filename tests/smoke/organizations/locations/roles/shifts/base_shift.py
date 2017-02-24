from datetime import timedelta, datetime
from app.helpers import normalize_to_midnight
from tests.smoke.organizations.locations.roles.base_role import BaseRole


class BaseShift(BaseRole):
    def setUp(self):
        # (if you are copying and pasting, update class title below)
        super(BaseShift, self).setUp()

        # create a span of time and only 2 shifts will exist within it
        today = normalize_to_midnight(datetime.utcnow())
        self.range_start = (today - timedelta(days=4)).isoformat()
        self.range_stop = (today + timedelta(days=4)).isoformat()

        # one unassigned
        unassigned_start = (today + timedelta(days=1, hours=8)).isoformat()
        unassigned_stop = (today + timedelta(days=1, hours=16)).isoformat()
        self.unassigned_shift = self.role.create_shift(
            start=unassigned_start, stop=unassigned_stop)

        # the other assigned
        self.coworker = self.role.create_worker(
            email="demo+coworker@7bridg.es",
            min_hours_per_workweek=20,
            max_hours_per_workweek=40)
        assigned_start = (today - timedelta(days=2, hours=15)).isoformat()
        assigned_stop = (today - timedelta(days=2, hours=7)).isoformat()
        self.assigned_shift = self.role.create_shift(
            start=assigned_start,
            stop=assigned_stop,
            user_id=self.coworker.get_id())

    def tearDown(self):
        # (if you are copying and pasting, update class title below)
        super(BaseShift, self).tearDown()
