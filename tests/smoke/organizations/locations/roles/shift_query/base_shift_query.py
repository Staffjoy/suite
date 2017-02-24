from datetime import datetime, timedelta
from app.helpers import normalize_to_midnight
from tests.smoke.organizations.locations.roles.base_role import BaseRole


class BaseShiftQuery(BaseRole):
    def setUp(self):
        # (if you are copying and pasting, update class title below)
        super(BaseShiftQuery, self).setUp()

        today = normalize_to_midnight(datetime.utcnow())
        self.query_start = (today + timedelta(days=2, hours=8)).isoformat()
        self.query_stop = (today + timedelta(days=2, hours=15)).isoformat()
        self.long_stop = (today + timedelta(days=3, hours=8)).isoformat()

        # the other assigned
        self.coworker = self.role.create_worker(
            email="demo+coworker@7bridg.es",
            min_hours_per_workweek=20,
            max_hours_per_workweek=40)

    def tearDown(self):
        # (if you are copying and pasting, update class title below)
        super(BaseShiftQuery, self).tearDown()
