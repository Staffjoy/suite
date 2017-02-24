from datetime import datetime, timedelta

from flask import current_app
from sqlalchemy import select, func, distinct, not_

from app import db
from app.constants import DAYS_OF_WEEK, WEEK_LENGTH
from app.plans import flex_plans, boss_plans

import user_model  # pylint: disable=relative-import
from app.models.location_model import Location
from app.models.role_model import Role
from app.models.role_to_user_model import RoleToUser

organization_admins = db.Table(
    "organization_admins",
    db.Column("organization_id", db.Integer,
              db.ForeignKey("organizations.id")),
    db.Column("user_id", db.Integer, db.ForeignKey("users.id")))


class Organization(db.Model):
    __tablename__ = "organizations"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256))
    active = db.Column(
        db.Boolean, default=False, server_default="0", nullable=False)
    created_at = db.Column(
        db.DateTime(), default=datetime.utcnow, nullable=False)
    enable_shiftplanning_export = db.Column(
        db.Boolean, default=False, server_default="0", nullable=False)
    enable_timeclock_default = db.Column(
        db.Boolean, default=False, server_default="0", nullable=False)
    enable_time_off_requests_default = db.Column(
        db.Boolean, default=False, server_default="0", nullable=False)
    day_week_starts = db.Column(
        db.String(256),
        db.Enum("monday", "tuesday", "wednesday", "thursday", "friday",
                "saturday", "sunday"),
        default="monday",
        server_default="monday",
        nullable=False)
    shifts_assigned_days_before_start = db.Column(
        db.Integer, default=4, server_default="4", nullable=False)
    workers_can_claim_shifts_in_excess_of_max = db.Column(
        db.Boolean, default=False, server_default="0", nullable=False)
    early_access = db.Column(
        db.Boolean, default=False, server_default="0", nullable=False)

    enterprise_access = db.Column(
        db.Boolean, default=False, server_default="0", nullable=False)

    #
    # Billing
    #

    # Override service and let org be paid forever. Use this for contracts, demo accounts, etc
    # When does the org get locked out?
    paid_until = db.Column(db.DateTime(), default=None)
    # Who's the one paying
    billing_user_id = db.Column(
        "billing_user_id", db.Integer, db.ForeignKey("users.id"), index=True)
    # Stripe unique subscription id (for that user)
    stripe_customer_id = db.Column(db.String(256))

    # The id of the plan, both here in the app and on stripe
    plan = db.Column(
        db.String(256),
        default="boss-v2",
        server_default="per-seat-v1",
        nullable=False)

    paid_labs_subscription_id = db.Column(db.String(256), nullable=True)

    # Can extend trial for certain people
    trial_days = db.Column(
        db.Integer, default=30, server_default="30", nullable=False)

    def in_trial(self):
        if self.paid():
            return False

        return self.created_at + timedelta(
            days=self.trial_days) > datetime.now()

    def trial_days_remaining(self):
        if self.paid():
            return 0
        delta = self.created_at + timedelta(
            days=self.trial_days) - datetime.now()
        # This takes floor, so add 1 to round up
        days = delta.days + 1
        if days < 0:
            return 0
        return days

    def active_billing_plan(self):
        """ Keep it simple """
        return self.paid_labs_subscription_id is not None

    def paid(self):
        """ Return whether the account is in good standings """
        if self.paid_until is None:
            return False
        return self.paid_until >= datetime.now()

    def worker_count(self):
        """ Return the number of workers in the account """
        query = select([func.count(distinct(
            user_model.User.id))])\
            .where(Organization.id == self.id)\
            .where(RoleToUser.archived == False)\
            .where(Organization.id == Location.organization_id)\
            .where(Location.id == Role.location_id)\
            .where(Role.id == RoleToUser.role_id)\
            .where(RoleToUser.user_id == user_model.User.id)\
            .select_from(RoleToUser)\
            .select_from(Role)\
            .select_from(Location)\
            .select_from(Organization)\
            .select_from(user_model.User)

        # Filter out demo account and Staffjoy emails
        for email in current_app.config.get("KPI_EMAILS_TO_EXCLUDE"):
            query = query.where(not_(user_model.User.email.like(email)))

        workers = db.session.execute(query).fetchone()[0]
        return workers

    def set_paid_days(self, days):
        if self.paid_until is None:
            start = datetime.now()
        elif self.paid_until < datetime.now():
            start = datetime.now()
        else:
            start = self.paid_until

        self.paid_until = start + timedelta(days=days)

    admins = db.relationship(
        "User",
        secondary=organization_admins,
        backref=db.backref("admin_of", lazy="dynamic"),
        lazy="dynamic")

    locations = db.relationship("Location", backref=db.backref("organization"))

    def intercom_settings(self):
        """ Data for Intercom to pass to user model IN BROWSER"""

        data = {
            "company_id": str(self.id),
            "name": self.name,
            "remote_created_at": int(self.created_at.strftime("%s")),
            "custom_attributes": {
                "active": self.active,
                "paid": self.paid(),
                "plan": self.plan,
                "enterprise_access": self.enterprise_access,
            }
        }

        return data

    def get_ordered_week(self):
        """returns a list of the days of the week where day_week_starts is first"""

        wrap_index = DAYS_OF_WEEK.index(self.day_week_starts)
        return DAYS_OF_WEEK[wrap_index:] + DAYS_OF_WEEK[:wrap_index]

    def is_plan_boss(self):
        """determines if the current plan is part of Staffjoy Boss"""
        return self.plan in boss_plans

    def is_plan_flex(self):
        """determines if the current plan is part of Staffjoy Flex"""
        return self.plan in flex_plans

    def get_week_start_from_datetime(self, current_day):
        """
        takes current_day and the org_id and returns a datetime for the start of
        the week

        DISCLAIMER - this does not normalize to midnight or pay attention to tzinfo
        """

        week_start_index = DAYS_OF_WEEK.index(self.day_week_starts)
        adjust_days = (WEEK_LENGTH - week_start_index + current_day.weekday()
                       ) % WEEK_LENGTH
        return current_day - timedelta(days=adjust_days)
