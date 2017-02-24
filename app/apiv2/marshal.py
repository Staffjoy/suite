import json

from flask_restful import fields

from app.models import User, Organization, RoleToUser
from app.caches import RoleToUserCache

# Due to circular import issues, all fields that  need to be marshalled go here

# Custom fields


class JsonField(fields.Raw):
    """ Decodes json """

    def format(self, value):
        return json.loads(value)


class HalfHourToHour(fields.Raw):
    """converts half-hour to hour granularity"""

    def format(self, value):
        return value / 2.0 if value else 0


class ShiftUserField(fields.Raw):
    """ get the user's name or email as a shift field"""

    def format(self, value):

        # I'm going to hell for this. It's cached.
        u = User.query.get(value)

        if u.name:
            return u.name
        else:
            return u.email


class RoleToUserToRoleId(fields.Raw):
    """
    take a role_to_user_id and get the corresponding
    role_id from it
    """

    def format(self, role_to_user_id):
        cache_data = RoleToUserCache.get(role_to_user_id)

        if cache_data is None:
            rtu = RoleToUser.query.get(role_to_user_id)
            cache_data = {"user_id": rtu.user_id, "role_id": rtu.role_id}
            RoleToUserCache.set(role_to_user_id, cache_data)

        return cache_data["role_id"]


class RoleToUserToUserId(fields.Raw):
    """
    take a role_to_user_id and get the corresponding
    user_id from it
    """

    def format(self, role_to_user_id):
        cache_data = RoleToUserCache.get(role_to_user_id)

        if cache_data is None:
            rtu = RoleToUser.query.get(role_to_user_id)
            cache_data = {"user_id": rtu.user_id, "role_id": rtu.role_id}
            RoleToUserCache.set(role_to_user_id, cache_data)

        return cache_data["user_id"]


class OrgPaidField(fields.Raw):
    def format(self, value):
        org = Organization.query.get(value)
        return org.paid()


user_fields = {
    "username": fields.String,
    "email": fields.String,
    "id": fields.Integer,
    "sudo": fields.Boolean,
    "confirmed": fields.Boolean,
    "name": fields.String,
    "member_since": fields.DateTime(dt_format="iso8601"),
    "last_seen": fields.DateTime(dt_format="iso8601"),
    "active": fields.Boolean,
    "phone_number": fields.String,
}

organization_fields = {
    "id": fields.Integer,
    "name": fields.String,
    "day_week_starts": fields.String,
    "active": fields.Boolean,
    "enable_shiftplanning_export": fields.Boolean,
    "enable_timeclock_default": fields.Boolean,
    "enable_time_off_requests_default": fields.Boolean,
    "shifts_assigned_days_before_start": fields.Integer,
    "workers_can_claim_shifts_in_excess_of_max": fields.Boolean,
    "paid": OrgPaidField(attribute="id"),
    "plan": fields.String,
    "created_at": fields.DateTime(dt_format="iso8601"),
    "early_access": fields.Boolean,
    "enterprise_access": fields.Boolean,
    "trial_days": fields.Integer,
    "paid_until": fields.DateTime(dt_format="iso8601"),
}

location_fields = {
    "id": fields.Integer,
    "archived": fields.Boolean,
    "name": fields.String,
    "organization_id": fields.Integer,
    "timezone": fields.String,
}

role_fields = {
    "id":
    fields.Integer,
    "name":
    fields.String,
    "location_id":
    fields.Integer,
    "archived":
    fields.Boolean,
    "enable_timeclock":
    fields.Boolean,
    "enable_time_off_requests":
    fields.Boolean,
    "min_hours_per_workday":
    HalfHourToHour(attribute="min_half_hours_per_workday"),
    "max_hours_per_workday":
    HalfHourToHour(attribute="max_half_hours_per_workday"),
    "min_hours_between_shifts":
    HalfHourToHour(attribute="min_half_hours_between_shifts"),
    "max_consecutive_workdays":
    fields.Integer,
}

role_to_user_fields = {
    "min_hours_per_workweek":
    HalfHourToHour(attribute="min_half_hours_per_workweek"),
    "max_hours_per_workweek":
    HalfHourToHour(attribute="max_half_hours_per_workweek"),
    "archived":
    fields.Boolean,
    "internal_id":
    fields.String,
    "working_hours":
    JsonField,
}

schedule_fields = {
    "id":
    fields.Integer,
    "role_id":
    fields.Integer,
    "state":
    fields.String,
    "demand":
    JsonField,
    "start":
    fields.DateTime(dt_format="iso8601"),
    "stop":
    fields.DateTime(dt_format="iso8601"),
    "min_shift_length_hour":
    HalfHourToHour(attribute="min_shift_length_half_hour"),
    "max_shift_length_hour":
    HalfHourToHour(attribute="max_shift_length_half_hour"),
    "created_at":
    fields.DateTime(dt_format="iso8601"),
    "last_update":
    fields.DateTime(dt_format="iso8601"),
    "chomp_start":
    fields.DateTime(dt_format="iso8601"),
    "chomp_end":
    fields.DateTime(dt_format="iso8601"),
}

preference_fields = {
    "preference": JsonField,
    "user_id": fields.Integer,
    "schedule_id": fields.Integer,
    "created_at": fields.DateTime(dt_format="iso8601"),
    "last_update": fields.DateTime(dt_format="iso8601"),
}

shift_fields = {
    "id": fields.Integer,
    "user_id": fields.Integer,
    "role_id": fields.Integer,
    "start": fields.DateTime(dt_format="iso8601"),
    "stop": fields.DateTime(dt_format="iso8601"),
    "published": fields.Boolean,
    "user_name": ShiftUserField(attribute="user_id"),
    "description": fields.String,
}

recurring_shift_fields = {
    "id": fields.Integer,
    "role_id": fields.Integer,
    "user_id": fields.Integer,
    "start_day": fields.String,
    "start_hour": fields.Integer,
    "start_minute": fields.Integer,
    "duration_minutes": fields.Integer,
    "quantity": fields.Integer,
}

tasking_schedule_fields = {
    "id": fields.Integer,
    "role_id": fields.Integer,
    "created_at": fields.DateTime(dt_format="iso8601"),
    "last_update": fields.DateTime(dt_format="iso8601"),
    "state": fields.String,
    "start": fields.DateTime(dt_format="iso8601"),
    "stop": fields.DateTime(dt_format="iso8601"),
    "chomp_start": fields.DateTime(dt_format="iso8601"),
    "chomp_end": fields.DateTime(dt_format="iso8601"),
    "mobius_start": fields.DateTime(dt_format="iso8601"),
    "mobius_end": fields.DateTime(dt_format="iso8601"),
}

timeclock_fields = {
    "id": fields.Integer,
    "role_id": fields.Integer,
    "user_id": fields.Integer,
    "start": fields.DateTime(dt_format="iso8601"),
    "stop": fields.DateTime(dt_format="iso8601"),
}

time_off_request_fields = {
    "id": fields.Integer,
    "role_id": RoleToUserToRoleId(attribute="role_to_user_id"),
    "user_id": RoleToUserToUserId(attribute="role_to_user_id"),
    "start": fields.DateTime(dt_format="iso8601"),
    "stop": fields.DateTime(dt_format="iso8601"),
    "approver_user_id": fields.Integer,
    "state": fields.String,
    "minutes_paid": fields.Integer,
}

api_key_fields = {
    "id": fields.Integer,
    "name": fields.String,
    "created_at": fields.DateTime(dt_format="iso8601"),
    "last_used": fields.DateTime(dt_format="iso8601")
}
