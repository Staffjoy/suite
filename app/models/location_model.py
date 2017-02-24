import pytz
from sqlalchemy import ForeignKey
from flask import render_template

from app import db

location_managers = db.Table(
    "location_managers",
    db.Column("location_id", db.Integer, db.ForeignKey("locations.id")),
    db.Column("user_id", db.Integer, db.ForeignKey("users.id")))


class Location(db.Model):
    __tablename__ = "locations"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256))
    organization_id = db.Column(db.Integer, ForeignKey('organizations.id'))
    roles = db.relationship("Role", backref=db.backref("location"))
    archived = db.Column(
        db.Boolean, default=False, server_default="0", nullable=False)
    timezone = db.Column(
        db.String(64), default="UTC", server_default="UTC", nullable=False)
    managers = db.relationship(
        "User",
        secondary=location_managers,
        backref=db.backref("manager_of", lazy="dynamic"),
        lazy="dynamic")

    def send_manager_email(self, subject, message, url):
        """
        sends an email to location managers, or the org admins if none exist
        """

        recipients = self.managers.all() or self.organization.admins.all()
        for user in recipients:
            user.send_email(subject,
                            render_template(
                                "email/notification-email.html",
                                user=user,
                                message=message,
                                url=url))

        return

    @property
    def timezone_pytz(self):
        return pytz.timezone(self.timezone)
