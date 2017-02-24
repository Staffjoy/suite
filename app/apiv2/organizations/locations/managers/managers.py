from flask import current_app
from flask_restful import marshal, reqparse, abort, Resource

from app import db
from app.constants import API_ENVELOPE
from app.models import User, Location, Organization
from app.apiv2.decorators import permission_location_manager, \
    verify_org_location
from app.apiv2.marshal import user_fields
from app.apiv2.email import alert_email


class LocationManagersApi(Resource):
    @permission_location_manager
    @verify_org_location
    def get(self, org_id, location_id):
        """ List all managers in this location"""
        response = {
            API_ENVELOPE: [],
        }

        location = Location.query.get_or_404(location_id)
        response[API_ENVELOPE] = map(
            lambda manager: marshal(manager, user_fields),
            location.managers.all())

        return response

    @permission_location_manager
    @verify_org_location
    def post(self, org_id, location_id):
        """ Add a user as a manager either by user id or email """
        parser = reqparse.RequestParser()
        parser.add_argument("email", type=str)
        parser.add_argument("id", type=int)
        parser.add_argument("name", type=str)
        parameters = parser.parse_args(strict=True)

        organization = Organization.query.get_or_404(org_id)
        location = Location.query.get_or_404(location_id)

        if parameters.get("id") is not None:
            user = User.query.get_or_404(parameters.get("id"))
        elif parameters.get("email") is not None:
            email = parameters.get("email")
            if "@" not in email:
                abort(400)

            # Check if user has email
            user = User.query.filter_by(email=email.lower()).first()
            # otherwise invite by email
            if user is None:
                user = User.create_and_invite(email,
                                              parameters.get("name"),
                                              organization.name)
        else:
            return {"message": "unable to identify user"}, 400

        if user.is_location_manager(location_id):
            return {"message": "user already an admin"}, 400

        location.managers.append(user)

        try:
            db.session.commit()
        except Exception as exception:
            db.session.rollback()
            current_app.logger.exception(str(exception))
            abort(400)

        alert_email(
            user, "You have been added as a %s manager at %s" % (
                location.name, organization.name),
            "You have been added as a manager at the %s location of %s." %
            (location.name, organization.name))

        return marshal(user, user_fields), 201
