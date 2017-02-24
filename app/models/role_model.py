from sqlalchemy import ForeignKey
from app import db


class Role(db.Model):
    __tablename__ = "roles"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256))
    location_id = db.Column(db.Integer, ForeignKey('locations.id'))
    members = db.relationship("RoleToUser", backref=db.backref("role"))
    archived = db.Column(
        db.Boolean, default=False, server_default="0", nullable=False)
    enable_timeclock = db.Column(
        db.Boolean, default=False, server_default="0", nullable=False)
    enable_time_off_requests = db.Column(
        db.Boolean, default=False, server_default="0", nullable=False)

    # scheduling properties
    min_half_hours_per_workday = db.Column(
        db.Integer, default=8, server_default="8", nullable=False)
    max_half_hours_per_workday = db.Column(
        db.Integer, default=16, server_default="16", nullable=False)
    min_half_hours_between_shifts = db.Column(
        db.Integer, default=24, server_default="24", nullable=False)
    max_consecutive_workdays = db.Column(
        db.Integer, default=6, server_default="6", nullable=False)
