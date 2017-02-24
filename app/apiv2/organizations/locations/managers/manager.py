from flask import current_app
from flask_restful import marshal, abort, reqparse, Resource, inputs

from app import db
from app.constants import API_ENVELOPE
from app.models import User, Organization, Location
from app.apiv2.decorators import permission_location_manager
from app.apiv2.marshal import user_fields
from app.apiv2.email import alert_email


class LocationManagerApi(Resource):
    @permission_location_manager
    def delete(self, org_id, location_id, user_id):
        """removes the user from the management position"""

        organization = Organization.query.get_or_404(org_id)
        location = Location.query.get_or_404(location_id)
        user = User.query.get_or_404(user_id)

        if not user.is_location_manager(location_id):
            return {"message": "User does not exist or is not a manager"}, 404

        location.managers.remove(user)

        try:
            db.session.commit()
        except Exception as exception:
            db.session.rollback()
            current_app.logger.exception(str(exception))
            abort(400)

        alert_email(
            user, "You have been removed as a %s manager at %s" %
            (location.name, organization.name),
            "You have been removed as a manager at the %s location of %s" %
            (location.name, organization.name))

        return {}, 204

    @permission_location_manager
    def get(self, org_id, location_id, user_id):
        user = User.query.get_or_404(user_id)

        if not user.is_location_manager(location_id):
            return {"message": "User does not exist or not a manager"}, 404

        response = {
            API_ENVELOPE: marshal(user, user_fields),
            "resources": [],
        }

        return response

    @permission_location_manager
    def patch(self, org_id, location_id, user_id):
        organization = Organization.query.get_or_404(org_id)
        user = User.query.get_or_404(user_id)

        if not user.is_location_manager(location_id):
            return {"message": "user does not exist or is not a manager"}, 404

        parser = reqparse.RequestParser()
        parser.add_argument("activateReminder", type=inputs.boolean)
        changes = parser.parse_args(strict=True)

        # Filter out null values
        changes = dict((k, v) for k, v in changes.iteritems() if v is not None)

        if len(changes) == 0:
            return {}, 204

        if "activateReminder" in changes:
            if user.active:
                return {"message": "This user is already active"}, 400

            user.send_activation_reminder(user, organization.name)

        return {}, 204
