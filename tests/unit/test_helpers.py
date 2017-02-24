from datetime import datetime

from app.helpers import timespans_overlap
from tests.unit.test_base import BasicsTestCase


class HelpersTestCase(BasicsTestCase):
    def test_timespans_overlap(self):
        time1 = 30
        time2 = 70
        time3 = 150
        time4 = 300

        # Case 1: B starts during A
        self.assertTrue(timespans_overlap(time1, time3, time2, time4))

        # Case 2: B ends during A
        self.assertTrue(timespans_overlap(time2, time4, time1, time3))

        # Case 3: B within A
        self.assertTrue(timespans_overlap(time1, time4, time2, time3))

        # no overlap
        self.assertFalse(timespans_overlap(time1, time2, time3, time4))

        # test with datetimes - no overlap
        dt1 = datetime(2016, 1, 1, 12, 30)
        dt2 = datetime(2016, 1, 1, 17, 30)
        dt3 = datetime(2016, 1, 1, 20, 0)
        dt4 = datetime(2016, 1, 1, 23, 30)

        self.assertFalse(timespans_overlap(dt1, dt2, dt3, dt4))
