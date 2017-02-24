from flask import g
from flask_restful import marshal, abort, inputs, reqparse, Resource

from app import db
from app.constants import API_ENVELOPE
from app.models import Organization, Role, RoleToUser
from app.apiv2.decorators import verify_org_location, \
    permission_location_member, permission_location_manager
from app.apiv2.marshal import user_fields, role_fields, role_to_user_fields


class RolesApi(Resource):
    @verify_org_location
    @permission_location_member
    def get(self, org_id, location_id):
        response = {
            API_ENVELOPE: [],
        }

        parser = reqparse.RequestParser()
        parser.add_argument("recurse", type=inputs.boolean, default=False)
        parser.add_argument("archived", type=inputs.boolean)
        args = parser.parse_args()
        args = dict((k, v) for k, v in args.iteritems() if v is not None)

        roles_query = Role.query.filter_by(location_id=location_id)

        # by default, only include active users
        if "archived" in args:
            roles_query = roles_query.filter_by(archived=args["archived"])

        roles = roles_query.all()
        response[API_ENVELOPE] = map(lambda role: marshal(role, role_fields),
                                     roles)

        if args["recurse"]:

            # Show all users in each location role
            for datum in response[API_ENVELOPE]:
                users_query = RoleToUser.query.filter_by(role_id=datum["id"])

                if "archived" in args:
                    users_query = users_query.filter_by(
                        archived=args["archived"])

                members = users_query.all()
                memberships = []

                for member in members:
                    rtu = marshal(member, role_to_user_fields)
                    rtu.update(marshal(member.user, user_fields))
                    memberships.append(rtu)

                datum.update({"users": memberships})

        return response

    @verify_org_location
    @permission_location_manager
    def post(self, org_id, location_id):
        parser = reqparse.RequestParser()
        parser.add_argument("name", type=str)
        parser.add_argument("enable_timeclock", type=inputs.boolean)
        parser.add_argument("enable_time_off_requests", type=inputs.boolean)
        parser.add_argument("min_hours_per_workday", type=int, default=4)
        parser.add_argument("max_hours_per_workday", type=int, default=8)
        parser.add_argument("min_hours_between_shifts", type=int, default=12)
        parser.add_argument("max_consecutive_workdays", type=int, default=6)
        parameters = parser.parse_args(strict=True)

        # Filter out null values
        parameters = dict((k, v) for k, v in parameters.iteritems()
                          if v is not None)

        organization = Organization.query.get_or_404(org_id)

        min_half_hours_per_workday = parameters.get(
            "min_hours_per_workday") * 2
        max_half_hours_per_workday = parameters.get(
            "max_hours_per_workday") * 2
        min_half_hours_between_shifts = parameters.get(
            "min_hours_between_shifts") * 2
        max_consecutive_workdays = parameters.get("max_consecutive_workdays")

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

        enable_timeclock = parameters.get(
            "enable_timeclock", organization.enable_timeclock_default)

        enable_time_off_requests = parameters.get(
            "enable_time_off_requests",
            organization.enable_time_off_requests_default)

        role = Role(
            name=parameters.get("name"),
            location_id=location_id,
            enable_timeclock=enable_timeclock,
            enable_time_off_requests=enable_time_off_requests,
            min_half_hours_per_workday=min_half_hours_per_workday,
            max_half_hours_per_workday=max_half_hours_per_workday,
            min_half_hours_between_shifts=min_half_hours_between_shifts,
            max_consecutive_workdays=max_consecutive_workdays, )
        db.session.add(role)

        try:
            db.session.commit()
            g.current_user.track_event("created_org")
            return marshal(role, role_fields), 201
        except:
            abort(500)
