from tests.unit.test_base import BasicsTestCase

from app import db
from app.models import RecurringShift, Shift2

import pytz
import datetime


class AppTestRecurringShift(BasicsTestCase):
    def test_create_shift2_for_schedule2(self):

        # create some recurring shifts
        # User 1 monday 9am to 2pm
        recurring_shift1 = RecurringShift(
            role_id=self.role.id,
            user_id=self.user1.id,
            start_day="monday",
            start_hour=9,
            start_minute=0,
            duration_minutes=300)

        # User 1 tuesday 10am to 4pm
        recurring_shift2 = RecurringShift(
            role_id=self.role.id,
            user_id=self.user1.id,
            start_day="tuesday",
            start_hour=10,
            start_minute=0,
            duration_minutes=360)

        # create a shift for User 1
        local_tz = pytz.timezone("America/Los_Angeles")
        default_tz = pytz.timezone("UTC")
        start_local = local_tz.localize(datetime.datetime(2016, 2, 1, 11, 0))
        stop_local = start_local + datetime.timedelta(hours=6)

        start_utc = start_local.astimezone(default_tz)
        stop_utc = stop_local.astimezone(default_tz)
        shift = Shift2(
            start=start_utc,
            stop=stop_utc,
            role_id=self.role.id,
            user_id=self.user1.id)

        db.session.add(recurring_shift1)
        db.session.add(recurring_shift2)
        db.session.add(shift)
        db.session.commit()

        # recurring_shift1 will be created, but since it overlaps with the shift,
        # it will be unassigned
        recurring_shift1.create_shift2_for_schedule2(self.schedule.id)

        # recurring_shift2 will be created and assigned to User 1
        recurring_shift2.create_shift2_for_schedule2(self.schedule.id)

        shifts_query = Shift2.query.filter(Shift2.start >= self.schedule.start,
                                           Shift2.start < self.schedule.stop)

        shifts_in_week = shifts_query.all()
        user1_shifts = shifts_query.filter_by(user_id=self.user1.id).all()

        # there should be 3 total shifts, 2 assigned to User 1
        assert len(user1_shifts) == 2
        assert len(shifts_in_week) == 3

        # find shift for recurring_shift1
        shift_start_utc = local_tz.localize(
            datetime.datetime(2016, 2, 1, recurring_shift1.start_hour,
                              recurring_shift1.start_minute)).astimezone(
                                  default_tz).replace(tzinfo=None)
        corresponding_shift1 = Shift2.query.filter_by(
            start=shift_start_utc).first()

        assert corresponding_shift1 is not None
        assert corresponding_shift1.user_id is None

        # find shift for recurring_shift2
        shift_start_utc = local_tz.localize(
            datetime.datetime(2016, 2, 2, recurring_shift2.start_hour,
                              recurring_shift2.start_minute)).astimezone(
                                  default_tz).replace(tzinfo=None)
        corresponding_shift2 = Shift2.query.filter_by(
            start=shift_start_utc).first()

        assert corresponding_shift2 is not None
        assert corresponding_shift2.user_id == self.user1.id

        # now test quantity
        # monday 9am to 2pm
        recurring_shift3 = RecurringShift(
            role_id=self.role.id,
            start_day="monday",
            start_hour=6,
            start_minute=0,
            duration_minutes=300,
            quantity=4)
        db.session.add(recurring_shift3)
        db.session.commit()

        recurring_shift3.create_shift2_for_schedule2(1)

        # find shift for recurring_shift1
        quantity_shift_start_utc = local_tz.localize(
            datetime.datetime(2016, 2, 1, recurring_shift3.start_hour,
                              recurring_shift3.start_minute)).astimezone(
                                  default_tz).replace(tzinfo=None)
        corresponding_shifts = Shift2.query.filter_by(
            start=quantity_shift_start_utc).all()

        assert len(corresponding_shifts) == recurring_shift3.quantity
        for shift_ in corresponding_shifts:
            assert shift_.user_id is None

    def test_has_overlaps(self):
        # create some recurring shifts for future comparison
        # all tests are with user 1 unless noted otherwise

        # User 1 monday 9am to 2pm
        recurring_shift1 = RecurringShift(
            role_id=1,
            user_id=1,
            start_day="monday",
            start_hour=9,
            start_minute=0,
            duration_minutes=300)

        # User 1 tuesday 10am to 4pm
        recurring_shift2 = RecurringShift(
            role_id=1,
            user_id=1,
            start_day="tuesday",
            start_hour=10,
            start_minute=0,
            duration_minutes=360)

        # User 2 sunday 11pm to 7am
        recurring_shift3 = RecurringShift(
            role_id=1,
            user_id=2,
            start_day="sunday",
            start_hour=23,
            start_minute=0,
            duration_minutes=480)

        db.session.add(recurring_shift1)
        db.session.add(recurring_shift2)
        db.session.add(recurring_shift3)
        db.session.commit()

        # User 1 wednesday 1:30pm to 9pm
        test_recurring_shift = RecurringShift(
            role_id=1,
            user_id=1,
            start_day="wednesday",
            start_hour=13,
            start_minute=30,
            duration_minutes=450)

        # User 1 monday 11:30am to 9pm
        test_overlapping_shift = RecurringShift(
            role_id=1,
            user_id=1,
            start_day="monday",
            start_hour=11,
            start_minute=30,
            duration_minutes=570)

        # User 1 10pm to 8am
        test_wraparound_no_overlap = RecurringShift(
            role_id=1,
            user_id=1,
            start_day="sunday",
            start_hour=22,
            start_minute=0,
            duration_minutes=600)

        # User 1 10pm to 10am
        test_wraparound_overlap = RecurringShift(
            role_id=1,
            user_id=1,
            start_day="sunday",
            start_hour=22,
            start_minute=0,
            duration_minutes=720)

        # User 2 monday 4am to 10am
        user2_recurring_shift = RecurringShift(
            role_id=1,
            user_id=2,
            start_day="monday",
            start_hour=4,
            start_minute=0,
            duration_minutes=360)

        # test that it doesn't overlap
        self.assertFalse(test_recurring_shift.has_overlaps())

        # this recurring shift will overlap
        self.assertTrue(test_overlapping_shift.has_overlaps())

        # test wraparound no overlap
        self.assertFalse(test_wraparound_no_overlap.has_overlaps())

        # test wraparound overlap
        self.assertTrue(test_wraparound_overlap.has_overlaps())

        # this shift will overlap with an existing shift that wraps around
        self.assertTrue(user2_recurring_shift.has_overlaps())
