from datetime import timedelta

from flask import current_app
from sqlalchemy import ForeignKey
import pytz

from app.caches import Shifts2Cache
from app.helpers import get_default_tz, timespans_overlap
from app import db, constants

import schedule2_model  # pylint: disable=relative-import
import organization_model  # pylint: disable=relative-import
import shift2_model  # pylint: disable=relative-import
from app.models.location_model import Location
from app.models.role_model import Role


class RecurringShift(db.Model):
    """
    a shift that is intended to persist each week - needs to be migrated
    into each schedule
    """

    __tablename__ = "recurring_shifts"
    id = db.Column(db.Integer, primary_key=True)
    role_id = db.Column(db.Integer, ForeignKey("roles.id"), nullable=False)
    user_id = db.Column(db.Integer, ForeignKey("users.id"))
    start_day = db.Column(
        db.String(256),
        db.Enum("monday", "tuesday", "wednesday", "thursday", "friday",
                "saturday", "sunday"),
        default="monday",
        server_default="monday",
        nullable=False)
    start_hour = db.Column(
        db.Integer, default=9, server_default="9", nullable=False)
    start_minute = db.Column(
        db.Integer, default=0, server_default="0", nullable=False)
    duration_minutes = db.Column(
        db.Integer, default=480, server_default="480", nullable=False)
    quantity = db.Column(
        db.Integer, default=1, server_default="1", nullable=False)

    def create_shift2_for_schedule2(self, schedule_id):
        """
        creates a shift2 for the week according to the recurring shift
        """

        # get org, location, and schedule models
        org = organization_model.Organization.query \
            .join(Location) \
            .join(Role) \
            .filter(
                Role.id == self.role_id,
                Location.id == Role.location_id,
                organization_model.Organization.id == Location.organization_id
            ) \
            .first()

        # get location for the timezone data
        location = Location.query \
            .join(Role) \
            .filter(
                Role.id == self.role_id,
                Location.id == Role.location_id
            ) \
            .first()

        schedule = schedule2_model.Schedule2.query.get(schedule_id)

        local_tz = location.timezone_pytz
        default_tz = get_default_tz()

        # get start and stop time for the shift
        start_local = default_tz.localize(schedule.start).astimezone(local_tz)

        # adjust start to fall on the correct day of the week
        ordered_week = org.get_ordered_week()
        adjust_days = ordered_week.index(self.start_day)

        start_local = start_local + timedelta(days=adjust_days)

        try:
            start_local = start_local.replace(
                hour=self.start_hour, minute=self.start_minute)
        except pytz.AmbiguousTimeError:
            start_local = start_local.replace(
                hour=self.start_hour, minute=self.start_minute, is_dst=False)

        stop_local = start_local + timedelta(minutes=self.duration_minutes)

        # convert start and end back to utc time
        start_utc = start_local.astimezone(default_tz).replace(tzinfo=None)
        stop_utc = stop_local.astimezone(default_tz).replace(tzinfo=None)

        published = (schedule.state == "published")

        for _ in range(self.quantity):

            new_shift = shift2_model.Shift2(
                start=start_utc,
                stop=stop_utc,
                role_id=self.role_id,
                published=published,
                user_id=self.user_id)

            # check if shift overlaps - make it unassigned if an overlap
            if self.user_id is not None:
                if new_shift.has_overlaps():
                    new_shift.user_id = None

            db.session.add(new_shift)

        db.session.commit()

        # flush the shift cache
        Shifts2Cache.delete(schedule_id)
        current_app.logger.info(
            "Created shift for recurring shift %s during schedule %s" %
            (self.id, schedule_id))

    def has_overlaps(self):
        """
        Returns True if a given recurring shift overlaps with the users recurring shifts
        """

        test_shift_start = (constants.DAYS_OF_WEEK.index(self.start_day) *
                            constants.MINUTES_PER_DAY) + (
                                self.start_hour * constants.MINUTES_PER_HOUR
                            ) + self.start_minute

        test_shift_end = test_shift_start + self.duration_minutes

        overlap_check = test_shift_end >= constants.MINUTES_PER_WEEK

        recurring_user_shifts = RecurringShift.query.filter(
            RecurringShift.id != self.id,
            RecurringShift.role_id == self.role_id,
            RecurringShift.user_id == self.user_id).all()

        for recurring_shift in recurring_user_shifts:

            compare_shift_start = (constants.DAYS_OF_WEEK.index(
                recurring_shift.start_day) * constants.MINUTES_PER_DAY) + (
                    recurring_shift.start_hour * constants.MINUTES_PER_HOUR
                ) + recurring_shift.start_minute

            compare_shift_end = compare_shift_start + recurring_shift.duration_minutes

            # first test with no wrapping
            if timespans_overlap(test_shift_start, test_shift_end,
                                 compare_shift_start, compare_shift_end):
                return True

            # test again with wraparound
            if overlap_check:
                if timespans_overlap(0, test_shift_end %
                                     constants.MINUTES_PER_WEEK,
                                     compare_shift_start, compare_shift_end):
                    return True

            # need to compare if the compare shift overlaps
            if compare_shift_end >= constants.MINUTES_PER_WEEK:
                if timespans_overlap(test_shift_start, test_shift_end, 0,
                                     compare_shift_end %
                                     constants.MINUTES_PER_WEEK):
                    return True

        return False
