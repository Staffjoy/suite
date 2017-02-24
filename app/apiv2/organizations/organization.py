from flask import g, current_app
from flask_restful import marshal, abort, inputs, reqparse, Resource
import iso8601

from app import db
from app.constants import API_ENVELOPE
from app.helpers import get_default_tz
from app.models import Organization
from app.apiv2.decorators import permission_org_member, permission_org_admin
from app.apiv2.marshal import organization_fields


class OrganizationApi(Resource):
    @permission_org_member
    def get(self, org_id):
        response = {
            API_ENVELOPE: {},
            "resources": ["admins", "locations", "workers"],
        }
        organization = Organization.query.get_or_404(org_id)

        response[API_ENVELOPE] = marshal(organization, organization_fields)

        return response

    @permission_org_admin
    def patch(self, org_id):
        parser = reqparse.RequestParser()
        parser.add_argument("name", type=str)
        parser.add_argument("active", type=inputs.boolean)
        parser.add_argument("shifts_assigned_days_before_start", type=int)
        parser.add_argument("enable_shiftplanning_export", type=inputs.boolean)
        parser.add_argument("enable_timeclock_default", type=inputs.boolean)
        parser.add_argument(
            "enable_time_off_requests_default", type=inputs.boolean)
        parser.add_argument("enterprise_access", type=inputs.boolean)
        parser.add_argument(
            "workers_can_claim_shifts_in_excess_of_max", type=inputs.boolean)
        parser.add_argument("early_access", type=inputs.boolean)
        parser.add_argument("trial_days", type=int)
        parser.add_argument("paid_until", type=str)

        changes = parser.parse_args(strict=True)
        # Filter out null values
        changes = dict((k, v) for k, v in changes.iteritems() if v is not None)

        # Throw 403 if non-sudo tries to update one of these.
        # It's a patch, not update, so non-sudo should not attempt this.
        sudo_only = [
            "enable_shiftplanning_export",
            "early_access",
            "enterprise_access",
            "trial_days",
            "paid_until",
        ]

        for key in sudo_only:
            if (not g.current_user.is_sudo()) and (key in changes):
                abort(403)

        org = Organization.query.get_or_404(org_id)
        default_tz = get_default_tz()

        #
        # Some verifications
        #

        # timing
        shifts_assigned_days_before_start = changes.get(
            "shifts_assigned_days_before_start",
            org.shifts_assigned_days_before_start)

        if shifts_assigned_days_before_start < 1:
            return {
                "message":
                "shifts_assigned_days_before_start must be greater than 0"
            }, 400
        if shifts_assigned_days_before_start > 100:
            return {
                "message":
                "shifts_assigned_days_before_start must be less than 100"
            }, 400

        trial_days = changes.get("trial_days", org.trial_days)
        if trial_days < 0:
            return {"messages": "trial_days cannot be less than 0"}

        if "paid_until" in changes:
            try:
                paid_until = iso8601.parse_date(changes.get("paid_until"))
            except iso8601.ParseError:
                return {
                    "message": "Paid until time needs to be in ISO 8601 format"
                }, 400
            else:
                paid_until = (paid_until + paid_until.utcoffset()).replace(
                    tzinfo=default_tz)

            changes["paid_until"] = paid_until.isoformat()

        for change, value in changes.iteritems():
            if value is not None:
                try:
                    setattr(org, change, value)
                    db.session.commit()
                except Exception as exception:
                    db.session.rollback()
                    current_app.logger.exception(str(exception))
                    abort(400)
        return changes
