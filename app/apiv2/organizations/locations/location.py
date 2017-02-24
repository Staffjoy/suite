from flask import g, current_app
from flask_restful import marshal, abort, inputs, reqparse, Resource

from app import db
from app.constants import API_ENVELOPE
from app.models import Location, Role, User
from app.apiv2.decorators import verify_org_location, \
    permission_location_member, permission_location_manager, \
    permission_org_admin
from app.apiv2.marshal import location_fields, role_fields, user_fields

from app.apiv2.organizations.locations.roles.role import RoleApi
from app.apiv2.organizations.locations.managers.manager import LocationManagerApi


class LocationApi(Resource):
    @verify_org_location
    @permission_location_member
    def get(self, org_id, location_id):
        response = {
            API_ENVELOPE: {},
            "resources": [
                "attendance", "managers", "shifts", "timeclocks",
                "timeoffrequests", "roles"
            ],
        }

        parser = reqparse.RequestParser()
        parser.add_argument("recurse", type=inputs.boolean, default=False)
        parser.add_argument("archived", type=inputs.boolean)
        args = parser.parse_args()
        args = dict((k, v) for k, v in args.iteritems() if v is not None)

        location = Location.query.get_or_404(location_id)
        response[API_ENVELOPE] = marshal(location, location_fields)

        if args["recurse"]:
            roles_query = Role.query.filter_by(location_id=location_id)

            if "archived" in args:
                roles_query = roles_query.filter_by(archived=args["archived"])

            roles = roles_query.all()
            response[API_ENVELOPE].update({
                "roles":
                map(lambda role: marshal(role, role_fields), roles)
            })

            # also include managers for the location
            managers = User.query.join(User.manager_of).filter(
                Location.id == location_id).all()
            response[API_ENVELOPE].update({
                "managers":
                map(lambda manager: marshal(manager, user_fields), managers)
            })

        return response

    @verify_org_location
    @permission_location_manager
    def patch(self, org_id, location_id):
        parser = reqparse.RequestParser()
        parser.add_argument("name", type=str)
        parser.add_argument("archived", type=inputs.boolean)
        changes = parser.parse_args(strict=True)

        # Filter out null values
        changes = dict((k, v) for k, v in changes.iteritems() if v is not None)

        if len(changes) == 0:
            return {}

        location = Location.query.get_or_404(location_id)

        if "archived" in changes:
            if not g.current_user.is_sudo():
                return {
                    "message":
                    "You do not have permission to modify 'archived'."
                }, 401

        elif location.archived:
            abort(400)

        for change, value in changes.iteritems():
            if value is not None:
                try:
                    setattr(location, change, value)
                    db.session.commit()
                except Exception as exception:
                    db.session.rollback()
                    current_app.logger.exception(str(exception))
                    abort(400)

        g.current_user.track_event("updated_org")
        return changes

    @verify_org_location
    @permission_org_admin
    def delete(self, org_id, location_id):
        """ Deletes a location by archiving it. """
        location = Location.query.get_or_404(location_id)
        managers = location.managers.all()
        roles = Role.query.filter_by(location_id=location_id).filter_by(
            archived=False).all()

        # remove managers
        manager_api = LocationManagerApi()
        for manager in managers:
            manager_api.delete(
                org_id=org_id, location_id=location_id, user_id=manager.id)

        role_api = RoleApi()
        for role in roles:
            role_api.delete(
                org_id=org_id, location_id=location_id, role_id=role.id)

        if location.archived:
            abort(400)

        location.archived = True

        try:
            db.session.commit()
        except Exception as exception:
            db.session.rollback()
            current_app.logger.exception(str(exception))
            abort(400)

        return {}, 204
