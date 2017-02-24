import json

from flask import g, current_app
from flask_restful import marshal, abort, inputs, reqparse, Resource

from app import db
from app.constants import API_ENVELOPE
from app.models import User, Organization, Location, Role, RoleToUser
from app.apiv2.decorators import verify_org_location_role, \
    permission_location_manager

from app.apiv2.marshal import user_fields, role_to_user_fields
from app.apiv2.email import alert_email
from app.apiv2.helpers import verify_days_of_week_struct


class RoleMembersApi(Resource):
    @verify_org_location_role
    @permission_location_manager
    def get(self, org_id, location_id, role_id):
        """ List all members in this role """

        parser = reqparse.RequestParser()
        parser.add_argument("archived", type=inputs.boolean)
        parameters = parser.parse_args(strict=True)
        parameters = dict((k, v) for k, v in parameters.iteritems()
                          if v is not None)

        response = {
            API_ENVELOPE: [],
        }
        users_query = RoleToUser.query.filter_by(role_id=role_id)

        # by default, only include active users
        if "archived" in parameters:
            users_query = users_query.filter_by(
                archived=parameters["archived"])

        members = users_query.all()

        for member in members:
            datum = {}
            datum.update(marshal(member.user, user_fields))
            datum.update(marshal(member, role_to_user_fields))
            response[API_ENVELOPE].append(datum)

        return response

    @verify_org_location_role
    @permission_location_manager
    def post(self, org_id, location_id, role_id):
        """ Add a user as a worker either by user id or email """

        role = Role.query.get_or_404(role_id)
        org = Organization.query.get_or_404(org_id)

        parser = reqparse.RequestParser()
        parser.add_argument("email", type=str)
        parser.add_argument("id", type=int)
        parser.add_argument("min_hours_per_workweek", type=int, required=True)
        parser.add_argument("max_hours_per_workweek", type=int, required=True)
        parser.add_argument("name", type=str)
        parser.add_argument("internal_id", type=str)
        parser.add_argument("working_hours", type=str)
        parameters = parser.parse_args(strict=True)

        if parameters.get("id") is not None:
            user = User.query.get_or_404(parameters.get("id"))
        elif parameters.get("email") is not None:
            email = parameters.get("email")

            # Check if valid email
            if "@" not in email:
                abort(400)

            # Check if user has email
            user = User.query.filter_by(email=email.lower().strip()).first()

            # otherwise invite by email
            if user is None:
                user = User.create_and_invite(email,
                                              parameters.get("name"), org.name)
        else:
            return {"message": "unable to identify user"}, 400

        # get min/max workweek values
        min_half_hours_per_workweek = parameters.get(
            "min_hours_per_workweek") * 2
        max_half_hours_per_workweek = parameters.get(
            "max_hours_per_workweek") * 2

        if min_half_hours_per_workweek > max_half_hours_per_workweek:
            return {
                "message":
                "min_hours_per_workweek cannot be greater than max_hours_per_workweek"
            }, 400

        if not (0 <= min_half_hours_per_workweek <= 336):
            return {
                "message": "min_hours_per_workweek cannot be less than 0"
            }, 400

        if not (0 <= max_half_hours_per_workweek <= 336):
            return {
                "message": "max_hours_per_workweek cannot be greater than 168"
            }, 400

        # check if the user already is in the role
        membership = RoleToUser.query.filter_by(role_id=role_id).filter_by(
            user_id=user.id).first()

        if membership:
            if membership.archived == False:
                return {"message": "user already in role"}, 400

            membership.archived = False

        else:
            membership = RoleToUser()
            membership.user = user
            membership.role = role

        membership.min_half_hours_per_workweek = min_half_hours_per_workweek
        membership.max_half_hours_per_workweek = max_half_hours_per_workweek

        # internal_id in post? I'll allow it
        if parameters.get("internal_id") is not None:
            membership.internal_id = parameters["internal_id"]

        if parameters.get("working_hours") is not None:
            try:
                working_hours = json.loads(parameters.get("working_hours"))
            except:
                return {
                    "message": "Unable to parse working hours json body"
                }, 400
            if working_hours is None:
                return {
                    "message": "Unable to parse working hours json body"
                }, 400
            if not verify_days_of_week_struct(working_hours, True):
                return {
                    "message": "working hours is improperly formatted"
                }, 400

            membership.working_hours = json.dumps(working_hours)

        try:
            db.session.commit()
        except Exception as exception:
            db.session.rollback()
            current_app.logger.exception(str(exception))
            abort(400)

        location = Location.query.get(location_id)
        organization = Organization.query.get(org_id)

        alert_email(
            user, "You have been added to %s on Staffjoy" % organization.name,
            "%s is using Staffjoy to manage its workforce, and you have been added to the team <b>%s</b> at the <b>%s</b> location."
            % (organization.name, role.name, location.name, ))

        data = {}
        data.update(marshal(user, user_fields))
        data.update(marshal(membership, role_to_user_fields))
        g.current_user.track_event("added_role_member")

        return data, 201
