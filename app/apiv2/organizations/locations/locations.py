from flask import current_app
from flask_restful import marshal, abort, inputs, reqparse, Resource
import pytz

from app import db
from app.constants import API_ENVELOPE
from app.models import Location, Role, User
from app.apiv2.decorators import permission_org_member, permission_org_admin
from app.apiv2.marshal import location_fields, role_fields, user_fields


class LocationsApi(Resource):
    @permission_org_member
    def get(self, org_id):
        response = {
            API_ENVELOPE: [],
        }

        parser = reqparse.RequestParser()
        parser.add_argument("recurse", type=inputs.boolean, default=False)
        parser.add_argument("archived", type=inputs.boolean)
        args = parser.parse_args()
        args = dict((k, v) for k, v in args.iteritems() if v is not None)

        locations_query = Location.query.filter_by(organization_id=org_id)

        # by default only include active locations
        if "archived" in args:
            locations_query = locations_query.filter_by(
                archived=args["archived"])

        locations = locations_query.all()
        response[API_ENVELOPE] = map(
            lambda location: marshal(location, location_fields), locations)

        if args["recurse"]:

            # Show all roles in each location
            for datum in response[API_ENVELOPE]:
                roles_query = Role.query.filter_by(location_id=datum["id"])

                if "archived" in args:
                    roles_query = roles_query.filter_by(
                        archived=args["archived"])

                roles = roles_query.all()
                datum.update({
                    "roles":
                    map(lambda role: marshal(role, role_fields), roles)
                })

                # Also add all managers for each location
                managers = User.query.join(User.manager_of).filter(
                    Location.id == datum["id"]).all()
                datum.update({
                    "managers":
                    map(lambda manager: marshal(manager, user_fields),
                        managers)
                })

        return response

    @permission_org_admin
    def post(self, org_id):
        parser = reqparse.RequestParser()
        parser.add_argument("name", type=str)
        parser.add_argument(
            "timezone",
            type=str,
            default=current_app.config.get("DEFAULT_TIMEZONE"))
        parameters = parser.parse_args(strict=True)

        timezone = parameters.get("timezone")

        try:
            pytz.timezone(timezone)
        except pytz.exceptions.UnknownTimeZoneError as zone:
            return {"message": "Unknown timezone specified: %s" % zone}, 400

        l = Location(
            name=parameters.get("name"),
            organization_id=org_id,
            timezone=timezone)
        db.session.add(l)
        try:
            db.session.commit()
            return marshal(l, location_fields), 201
        except Exception as exception:
            db.session.rollback()
            current_app.logger.exception(str(exception))
            abort(400)
