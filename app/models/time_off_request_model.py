from datetime import datetime

from flask import current_app
from sqlalchemy import ForeignKey, and_, or_

from app import db
from app.caches import Shifts2Cache

import schedule2_model  # pylint: disable=relative-import
import shift2_model  # pylint: disable=relative-import
from app.models.role_to_user_model import RoleToUser


class TimeOffRequest(db.Model):
    __tablename__ = "timeoffrequests"
    id = db.Column(db.Integer, primary_key=True)
    role_to_user_id = db.Column(
        db.Integer,
        ForeignKey("roles_to_users.id"),
        index=True,
        nullable=False)
    start = db.Column(db.DateTime(), index=True, nullable=False)
    stop = db.Column(db.DateTime(), index=True, nullable=False)
    approver_user_id = db.Column("user_id", db.Integer,
                                 db.ForeignKey("users.id"))
    state = db.Column(
        db.String(256),
        db.Enum(
            "approved_paid",
            "approved_unpaid",
            "sick",
            "denied", ),
        index=True)
    minutes_paid = db.Column(
        db.Integer, default=0, server_default="0", nullable=False)

    def unassign_overlapping_shifts(self):
        rtu = RoleToUser.query.get(self.role_to_user_id)

        # unassign any overlapping shifts
        overlapping_shifts = shift2_model.Shift2.query \
            .filter(
                shift2_model.Shift2.role_id == rtu.role_id,
                shift2_model.Shift2.user_id == rtu.user_id,
                shift2_model.Shift2.start >= datetime.utcnow(),
                or_(
                    # Case 1: test_shift is within time off request
                    and_(
                        shift2_model.Shift2.start <= self.start,
                        shift2_model.Shift2.stop >= self.stop
                    ),
                    # Case 2: a  shift starts during time off request
                    and_(
                        shift2_model.Shift2.start >= self.start,
                        shift2_model.Shift2.start < self.stop,
                    ),
                    # Case 3: a shift ends during time off request
                    and_(
                        shift2_model.Shift2.stop > self.start,
                        shift2_model.Shift2.stop <= self.stop
                    )
                )
            ).all()

        for shift in overlapping_shifts:
            current_app.logger.info(
                "Setting shift %s to unassigned because it overlaps with an approved time off request for User %s"
                % (shift.id, shift.user_id))
            shift.user_id = None

            # clear cache too
            schedule = schedule2_model.Schedule2.query \
                .filter(
                    schedule2_model.Schedule2.role_id == rtu.role_id,
                    schedule2_model.Schedule2.start <= shift.start,
                    schedule2_model.Schedule2.stop > shift.start,
                ).first()

            if schedule is not None:
                Shifts2Cache.delete(schedule.id)

    def has_overlaps(self):
        """ makes sure the test_time_off_request doesn't overlap with any other ones by the same role to user"""

        # this query returns all time off requests that overlap with the test time off request
        overlapping_time_off_requests = TimeOffRequest.query \
            .filter(
                TimeOffRequest.role_to_user_id == self.role_to_user_id,
                TimeOffRequest.id != self.id,
                or_(
                    # Case 1: test_time_off_request is within another time off request
                    and_(
                        TimeOffRequest.start <= self.start,
                        TimeOffRequest.stop >= self.stop
                    ),
                    # Case 2: another time off request starts during test_time_off_request
                    and_(
                        TimeOffRequest.start >= self.start,
                        TimeOffRequest.start < self.stop,
                    ),
                    # Case 3: another time off request ends during test_time_off_request
                    and_(
                        TimeOffRequest.stop > self.start,
                        TimeOffRequest.stop <= self.stop
                    )
                )
            ).all()

        length = len(overlapping_time_off_requests)

        if length > 1:
            raise Exception(
                "Multiple overlapping time off requests detected for role_to_user_id %s"
                % self.role_to_user_id)

        return length > 0
