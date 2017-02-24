from datetime import datetime, timedelta
from collections import defaultdict
from copy import deepcopy

from sqlalchemy import ForeignKey, and_, or_

from app import db, constants
from app.helpers import normalize_to_midnight, get_default_tz

import schedule2_model  # pylint: disable=relative-import
import organization_model  # pylint: disable=relative-import
from app.models.location_model import Location
from app.models.role_model import Role
from app.models.role_to_user_model import RoleToUser


class Shift2(db.Model):
    """introduced for apiv2"""

    MAX_DESCRIPTION_LENGTH = 256

    __tablename__ = "shifts2"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, ForeignKey("users.id"))
    role_id = db.Column(db.Integer, ForeignKey("roles.id"), nullable=False)
    start = db.Column(
        db.DateTime(), default=datetime.utcnow, index=True, nullable=False)
    stop = db.Column(
        db.DateTime(), default=datetime.utcnow, index=True, nullable=False)
    published = db.Column(
        db.Boolean, default=False, server_default="0", nullable=False)
    created_at = db.Column(db.DateTime(), default=datetime.utcnow)
    last_update = db.Column(db.DateTime(), onupdate=datetime.utcnow)
    description = db.Column(db.String(256))

    def get_schedule(self):
        """returns the schedule model that the shift takes place during"""

        return schedule2_model.Schedule2.query.filter(
            schedule2_model.Schedule2.role_id == self.role_id,
            schedule2_model.Schedule2.start <= self.start,
            schedule2_model.Schedule2.stop > self.stop).first()

    @property
    def is_in_past(self):
        """determines whether the shift is in the past"""

        return datetime.utcnow() >= self.start

    def has_overlaps(self):
        """
        checks if this shift overlaps with any others

        unassigned shifts will not be considered for overlapping
        """

        if self.user_id is None:
            return False

        overlapping_shifts = Shift2.query \
            .filter(
                Shift2.role_id == self.role_id,
                Shift2.user_id == self.user_id,
                Shift2.id != self.id,
                or_(
                    # Case 1: test_shift is within another shift
                    and_(
                        Shift2.start <= self.start,
                        Shift2.stop >= self.stop
                    ),
                    # Case 2: another shift starts during test_shift
                    and_(
                        Shift2.start >= self.start,
                        Shift2.start < self.stop,
                    ),
                    # Case 3: another shift ends during test_shift
                    and_(
                        Shift2.stop > self.start,
                        Shift2.stop <= self.stop
                    )
                )
            ).all()

        return len(overlapping_shifts) > 0

    def is_within_caps(self, user_id):
        """
        does the addition of this shift exceed the user's hourly caps
        """

        role = Role.query.get(self.role_id)
        location = role.location
        org = location.organization
        role_to_user = RoleToUser.query.filter_by(
            role_id=self.role_id, user_id=user_id, archived=False).first()

        # archived users should not qualify
        if role_to_user is None:
            return False

        min_seconds_shift_gap = role.min_half_hours_between_shifts / constants.HALF_HOUR_TO_HOUR * constants.SECONDS_PER_HOUR
        max_seconds_workday = role.max_half_hours_per_workday / constants.HALF_HOUR_TO_HOUR * constants.SECONDS_PER_HOUR
        max_seconds_workweek = role_to_user.max_half_hours_per_workweek / constants.HALF_HOUR_TO_HOUR * constants.SECONDS_PER_HOUR

        default_tz = get_default_tz()
        local_tz = role.location.timezone_pytz

        # get schedule that exists during this shift
        schedule = self.get_schedule()

        # schedule may not exist - in which case must artificially determine search bounds and get shifts
        if schedule is None:
            local_start = default_tz.localize(self.start).astimezone(local_tz)

            # these values correspond to what the schedules date range would be
            start = normalize_to_midnight(
                org.get_week_start_from_datetime(local_start)).astimezone(
                    default_tz)
            stop = normalize_to_midnight((
                start + timedelta(days=constants.WEEK_LENGTH, hours=1)
            ).astimezone(local_tz)).astimezone(default_tz).replace(tzinfo=None)

            start = start.replace(tzinfo=None)

        # create same variables for parity
        else:
            start = schedule.start
            stop = schedule.stop

        # now get full range for query - need to know beyond just start/stop for
        # measuring consecutive days off
        query_start = start - timedelta(days=role.max_consecutive_workdays)
        query_stop = stop + timedelta(days=role.max_consecutive_workdays)

        # need localized start/end of the week/schedule
        week_start_local = default_tz.localize(start).astimezone(local_tz)
        week_stop_local = default_tz.localize(stop).astimezone(local_tz)

        # need to get all shifts that occur during the schedule
        # but also need those that extend beyond
        shifts = Shift2.query \
            .filter(
                Shift2.role_id == self.role_id,
                Shift2.user_id == user_id,
                Shift2.start >= query_start,
                Shift2.start < query_stop,
                Shift2.id != self.id,
            ).all()

        # time to do some comparisons

        # add self to the shifts and then sort
        # it's important to exclude the shift from the query, and 
        # then add it separately there are cases where it could be 
        # double counted, which would be bad
        shifts.append(self)
        shifts.sort(key=lambda x: x.start)

        workday_totals = defaultdict(int)
        consecutive_days = 0

        previous_stop = None
        current_date = None
        next_date = None

        for shift in shifts:
            shift_start_local = default_tz.localize(
                shift.start).astimezone(local_tz)
            shift_stop_local = default_tz.localize(
                shift.stop).astimezone(local_tz)

            # increment consecutive days if needed
            if shift_start_local.day == next_date:
                consecutive_days += 1

            # reset it if not consecutive days AND it's not on the same day as already credited
            elif shift_start_local.day != current_date:
                consecutive_days = 0

            # need to collect more data for the shifts that occur during the workweek
            if (start <= shift.start < stop) or (start <= shift.stop <= stop):

                # shift starts and ends on the same day
                if shift_stop_local.day == shift_start_local.day:
                    workday_totals[shift_start_local.day] += int(
                        (shift.stop - shift.start).total_seconds())

                # shift splits between midnight
                else:
                    split = normalize_to_midnight(shift_stop_local)

                    # account for case where shift overlaps from or into another week
                    if week_start_local <= shift_start_local <= week_stop_local:
                        workday_totals[shift_start_local.day] += int(
                            (split - shift_start_local).total_seconds())

                    if week_start_local <= shift_stop_local <= week_stop_local:
                        workday_totals[shift_stop_local.day] += int(
                            (shift_stop_local - split).total_seconds())

            # check time between shifts
            if previous_stop:
                if int((shift.start - previous_stop
                        ).total_seconds()) < min_seconds_shift_gap:
                    return False

            # consecutive days
            if consecutive_days > role.max_consecutive_workdays:
                return False

            previous_stop = shift.stop
            next_date = (shift_start_local + timedelta(days=1)).day
            current_date = shift_start_local.day

        # total hours per workday is too high
        if sum(workday_totals.values()) > max_seconds_workweek:
            return False

        # shift is too long for a given workday
        for key in workday_totals:
            if workday_totals[key] > max_seconds_workday:
                return False

        return True  # Does not defy caps :-)

    def get_users_within_caps(self, allow_past=False):
        """
        calls get_all_eligible_users and only returns the users within
        their defined limits
        """

        within_caps, _ = self.get_all_eligible_users(allow_past=allow_past)
        return within_caps

    def get_all_eligible_users(self, allow_past=False):
        """
        returns all users that are able to claim or be assigned a shift

        returns a tuple: ([users within caps], [users exceeding their caps])
        """

        # get org
        org = organization_model.Organization.query \
            .join(Location) \
            .join(Role) \
            .filter(
                Role.id == self.role_id,
                Location.id == Role.location_id,
                organization_model.Organization.id == Location.organization_id
            ) \
            .first()

        role_users = RoleToUser.query.filter_by(
            role_id=self.role_id, archived=False).all()

        within_caps = []
        exceeds_caps = []

        for role_user in role_users:
            shift_copy = deepcopy(self)

            # the user cannot claim the shift if it overlaps
            if role_user.user_id != shift_copy.user_id:
                shift_copy.user_id = role_user.user_id

                # check if in past if needed
                if not allow_past:
                    if shift_copy.is_in_past:
                        continue

                # check for overlap
                if shift_copy.has_overlaps():
                    continue

            # exceeds caps
            if (org.is_plan_boss() and
                    not org.workers_can_claim_shifts_in_excess_of_max and
                    not shift_copy.is_within_caps(role_user.user_id)):
                exceeds_caps.append(role_user.user)

            # within caps
            else:
                within_caps.append(role_user.user)

        return within_caps, exceeds_caps
