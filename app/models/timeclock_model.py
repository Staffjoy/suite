from datetime import datetime
from sqlalchemy import ForeignKey
from sqlalchemy.sql import and_, or_
from app import db


class Timeclock(db.Model):
    __tablename__ = "timeclocks"
    id = db.Column(db.Integer, primary_key=True)
    role_id = db.Column(db.Integer, ForeignKey("roles.id"), index=True)
    user_id = db.Column(
        db.Integer, ForeignKey("users.id"), index=True, nullable=False)
    start = db.Column(
        db.DateTime(), default=datetime.utcnow, index=True, nullable=False)
    stop = db.Column(db.DateTime(), default=None)

    def has_overlaps(self):
        """ makes sure the timeclock_test doesn't overlaps with any other ones by the same user role """

        # can't overlap if only 1 data point
        if self.stop is None:
            return False

        # this query returns all timeclocks that overlap with the test timeclock
        overlapping_timeclocks = Timeclock.query \
            .filter(
                Timeclock.role_id == self.role_id,
                Timeclock.user_id == self.user_id,
                Timeclock.id != self.id,
                or_(
                    # Case 1: self is within another timeclock
                    and_(
                        Timeclock.start <= self.start,
                        Timeclock.stop >= self.stop
                    ),
                    # Case 2: another timeclock starts during self
                    and_(
                        Timeclock.start >= self.start,
                        Timeclock.start < self.stop
                    ),
                    # Case 3: another timeclock ends during self
                    and_(
                        Timeclock.stop > self.start,
                        Timeclock.stop <= self.stop
                    )
                )
            ).all()

        return len(overlapping_timeclocks) > 0
