from flask import g, current_app
from flask_restful import marshal, abort, inputs, reqparse, Resource

from app import db
from app.constants import API_ENVELOPE
from app.models import Role, RoleToUser, Location
from app.apiv2.decorators import verify_org_location_role, \
    permission_location_member, permission_location_manager
from app.apiv2.marshal import user_fields, role_fields, role_to_user_fields

from app.apiv2.organizations.locations.roles.users.user import RoleMemberApi


class RoleApi(Resource):
    @verify_org_location_role
    @permission_location_member
    def get(self, org_id, location_id, role_id):
        response = {
            API_ENVELOPE: {},
            "resources": ["recurringshifts", "schedules", "shifts", "users"],
        }

        parser = reqparse.RequestParser()
        parser.add_argument("recurse", type=inputs.boolean, default=False)
        parser.add_argument("archived", type=inputs.boolean)
        args = parser.parse_args()
        args = dict((k, v) for k, v in args.iteritems() if v is not None)

        role = Role.query.get_or_404(role_id)
        response[API_ENVELOPE] = marshal(role, role_fields)

        if args["recurse"]:
            rtu_query = RoleToUser.query.filter_by(role_id=role_id)

            if "archived" in args:
                rtu_query = rtu_query.filter_by(archived=args["archived"])

            members = rtu_query.all()
            memberships = []

            for member in members:
                rtu = marshal(member, role_to_user_fields)
                rtu.update(marshal(member.user, user_fields))
                memberships.append(rtu)

            response[API_ENVELOPE].update({"users": memberships})

        return response

    @verify_org_location_role
    @permission_location_manager
    def patch(self, org_id, location_id, role_id):
        parser = reqparse.RequestParser()
        parser.add_argument("name", type=str)
        parser.add_argument("enable_timeclock", type=inputs.boolean)
        parser.add_argument("enable_time_off_requests", type=inputs.boolean)
        parser.add_argument("archived", type=inputs.boolean)
        parser.add_argument("min_hours_per_workday", type=int)
        parser.add_argument("max_hours_per_workday", type=int)
        parser.add_argument("min_hours_between_shifts", type=int)
        parser.add_argument("max_consecutive_workdays", type=int)
        changes = parser.parse_args(strict=True)

        # Filter out null values
        changes = dict((k, v) for k, v in changes.iteritems() if v is not None)

        role = Role.query.get_or_404(role_id)

        if "archived" in changes:
            if not g.current_user.is_sudo():
                return {
                    "message":
                    "You do not have permission to modify 'archived'."
                }, 401

            location = Location.query.get_or_404(location_id)
            if location.archived:
                return {"message": "The parent location is archived."}, 400

        elif role.archived:
            abort(400)

        max_consecutive_workdays = changes.get("max_consecutive_workdays",
                                               role.max_consecutive_workdays)

        if "min_hours_per_workday" in changes:
            min_half_hours_per_workday = changes["min_hours_per_workday"] * 2
        else:
            min_half_hours_per_workday = role.min_half_hours_per_workday

        if "max_hours_per_workday" in changes:
            max_half_hours_per_workday = changes["max_hours_per_workday"] * 2
        else:
            max_half_hours_per_workday = role.max_half_hours_per_workday

        if "min_hours_between_shifts" in changes:
            min_half_hours_between_shifts = changes[
                "min_hours_between_shifts"] * 2
        else:
            min_half_hours_between_shifts = role.min_half_hours_between_shifts

        # now verification
        if min_half_hours_per_workday > max_half_hours_per_workday:
            return {
                "message":
                "min_hours_per_workday cannot be greater than max_hours_per_workday"
            }, 400

        if not (1 <= min_half_hours_per_workday <= 48):
            return {
                "message": "min_hours_per_workday must be between 1 and 24"
            }, 400

        if not (1 <= max_half_hours_per_workday <= 48):
            return {
                "message": "max_hours_per_workday must be between 1 and 24"
            }, 400

        if not (0 <= min_half_hours_between_shifts <= 48):
            return {
                "message": "min_hours_between_shifts must be between 0 and 24"
            }, 400

        if not (4 <= max_consecutive_workdays <= 13):
            return {
                "message": "max_consecutive_workdays must be between 4 and 13"
            }, 400

        # convert to the correct db column being updated
        if "min_hours_per_workday" in changes:
            del changes["min_hours_per_workday"]
            changes["min_half_hours_per_workday"] = min_half_hours_per_workday

        if "max_hours_per_workday" in changes:
            del changes["max_hours_per_workday"]
            changes["max_half_hours_per_workday"] = max_half_hours_per_workday

        if "min_hours_between_shifts" in changes:
            del changes["min_hours_between_shifts"]
            changes[
                "min_half_hours_between_shifts"] = min_half_hours_between_shifts

        for change, value in changes.iteritems():
            if value is not None:
                try:
                    setattr(role, change, value)
                    db.session.commit()
                except Exception as exception:
                    db.session.rollback()
                    current_app.logger.exception(str(exception))
                    abort(400)

        g.current_user.track_event("updated_role")
        return changes

    @verify_org_location_role
    @permission_location_manager
    def delete(self, org_id, location_id, role_id):
        role = Role.query.get_or_404(role_id)

        # only need to archive active members
        assocs = RoleToUser.query \
            .filter_by(role_id=role_id) \
            .filter_by(archived=False) \
            .all()

        roleMemberApi = RoleMemberApi()
        for assoc in assocs:
            roleMemberApi.delete(
                org_id=org_id,
                location_id=location_id,
                role_id=role_id,
                user_id=assoc.user_id)

        if role.archived:
            abort(400)

        role.archived = True

        try:
            db.session.commit()
        except Exception as exception:
            db.session.rollback()
            current_app.logger.exception(str(exception))
            abort(400)

        g.current_user.track_event("deleted_role")
        return {}, 204
