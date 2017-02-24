from datetime import timedelta, datetime
from app.helpers import normalize_to_midnight
from tests.smoke.organizations.locations.roles.base_role import BaseRole


class BaseSchedule(BaseRole):
    def setUp(self):
        # (if you are copying and pasting, update class title below)
        super(BaseSchedule, self).setUp()

        today = normalize_to_midnight(datetime.utcnow())
        self.range_start = (today + timedelta(days=7)).isoformat()
        self.range_stop = (today + timedelta(days=14)).isoformat()

        self.demand = {
            "monday": [
                0, 0, 0, 0, 0, 0, 0, 0, 3, 6, 10, 13, 12, 12, 12, 12, 13, 11,
                8, 6, 4, 2, 0, 0
            ],
            "tuesday": [
                0, 0, 0, 0, 0, 0, 0, 0, 2, 6, 9, 9, 9, 10, 12, 13, 13, 11, 7,
                5, 4, 2, 0, 0
            ],
            "wednesday": [
                0, 0, 0, 0, 0, 0, 0, 0, 3, 6, 10, 10, 11, 12, 12, 12, 12, 11,
                9, 6, 5, 2, 0, 0
            ],
            "thursday": [
                0, 0, 0, 0, 0, 0, 0, 0, 3, 6, 7, 11, 11, 11, 9, 9, 10, 9, 5, 3,
                3, 2, 0, 0
            ],
            "friday": [
                0, 0, 0, 0, 0, 0, 0, 0, 2, 2, 7, 9, 9, 10, 12, 12, 12, 8, 7, 5,
                3, 2, 0, 0
            ],
            "saturday": [
                0, 0, 0, 0, 0, 0, 0, 0, 2, 3, 7, 7, 7, 7, 7, 7, 6, 5, 4, 2, 2,
                1, 0, 0
            ],
            "sunday": [
                0, 0, 0, 0, 0, 0, 0, 0, 1, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3, 2, 2,
                1, 0, 0
            ]
        }

    def tearDown(self):
        # (if you are copying and pasting, update class title below)
        super(BaseSchedule, self).tearDown()
