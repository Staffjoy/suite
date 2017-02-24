from datetime import datetime, timedelta
from app import db
from app.helpers import normalize_to_midnight
from app.models import Timeclock
from tests.unit.test_base import BasicsTestCase


class AppTestTimeclock(BasicsTestCase):
    def test_has_overlaps(self):
        # create some past timeclocks for testing
        # all tests are with user 1 unless noted otherwise

        # start from a week ago
        utcnow = datetime.utcnow()
        time_base = normalize_to_midnight(utcnow) - timedelta(days=7)

        # make some timeclocks - all occur on consecutive days
        t1_start = time_base + timedelta(hours=8)
        t1_stop = time_base + timedelta(hours=15)
        timeclock1 = Timeclock(
            role_id=1, user_id=1, start=t1_start, stop=t1_stop)

        t2_start = time_base + timedelta(days=1, hours=4)
        t2_stop = time_base + timedelta(days=1, hours=11)
        timeclock2 = Timeclock(
            role_id=1, user_id=1, start=t2_start, stop=t2_stop)

        t3_start = time_base + timedelta(days=2, hours=8)
        t3_stop = time_base + timedelta(days=2, hours=17)
        timeclock3 = Timeclock(
            role_id=1, user_id=1, start=t3_start, stop=t3_stop)

        # and they just clocked in for a new shift
        timeclock_now = Timeclock(role_id=1, user_id=1, start=utcnow)

        db.session.add(timeclock1)
        db.session.add(timeclock2)
        db.session.add(timeclock3)
        db.session.add(timeclock_now)
        db.session.commit()

        # this timeclock doesn't overlap
        no_overlap_start = time_base + timedelta(days=4, hours=5)
        no_overlap_stop = time_base + timedelta(days=4, hours=12)
        no_overlap_timeclock = Timeclock(
            role_id=1, user_id=1, start=no_overlap_start, stop=no_overlap_stop)
        self.assertFalse(no_overlap_timeclock.has_overlaps())

        # timeclock starting during one will fail
        # starts during timeclock1 (day 0, 8 - 15)
        start_within_start = time_base + timedelta(hours=12)
        start_within_stop = time_base + timedelta(hours=18)
        tc_start_within = Timeclock(
            role_id=1,
            user_id=1,
            start=start_within_start,
            stop=start_within_stop)
        self.assertTrue(tc_start_within.has_overlaps())

        # timeclock ending during one will fail
        # ends during timeclock2 (day 1, 4 - 11)
        ends_within_start = time_base + timedelta(days=1, hours=2)
        ends_within_stop = time_base + timedelta(days=1, hours=10)
        tc_ends_within = Timeclock(
            role_id=1,
            user_id=1,
            start=ends_within_start,
            stop=ends_within_stop)
        self.assertTrue(tc_ends_within.has_overlaps())

        # timeclock within another will fail
        # surrounds timeclock3, (day2, 8 - 17)
        surrounds_start = time_base + timedelta(days=2, hours=6)
        surrounds_stop = time_base + timedelta(days=2, hours=19)
        tc_surrounds = Timeclock(
            role_id=1, user_id=1, start=surrounds_start, stop=surrounds_stop)
        self.assertTrue(tc_surrounds.has_overlaps())

        # creating a timeclock around an active one will fail
        active_start = utcnow - timedelta(hours=4)
        active_stop = utcnow + timedelta(hours=4)
        tc_during_active = Timeclock(
            role_id=1, user_id=1, start=active_start, stop=active_stop)
        self.assertTrue(tc_during_active.has_overlaps())
