from datetime import datetime, timedelta
from app.helpers import normalize_to_midnight
from tests.smoke.organizations.locations.roles.users.base_user import BaseWorker


class BaseTimeOffRequest(BaseWorker):
    def setUp(self):
        # (if you are copying and pasting, update class title below)
        super(BaseTimeOffRequest, self).setUp()

        today = normalize_to_midnight(datetime.utcnow())
        self.range_start = today.isoformat()
        self.range_stop = (today + timedelta(days=10)).isoformat()

        # create a time off request for testing against
        next_week_str = (today + timedelta(days=7)).strftime("%Y-%m-%d")
        self.time_off_request = self.worker.create_time_off_request(
            date=next_week_str)

    def tearDown(self):
        # (if you are copying and pasting, update class title below)
        super(BaseTimeOffRequest, self).tearDown()
