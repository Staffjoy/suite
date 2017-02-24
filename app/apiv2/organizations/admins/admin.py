from flask import current_app
from flask_restful import marshal, abort, reqparse, Resource, inputs

from app import db
from app.constants import API_ENVELOPE
from app.models import User, Organization
from app.apiv2.email import alert_email
from app.apiv2.decorators import permission_org_admin, verify_org_admin
from app.apiv2.marshal import user_fields


class OrgAdminApi(Resource):
    @permission_org_admin
    @verify_org_admin
    def delete(self, org_id, user_id):
        organization = Organization.query.get_or_404(org_id)
        user = User.query.get_or_404(user_id)

        if not user.is_org_admin(org_id):
            return {"message": "user does not exist or not an admin"}, 404

        organization.admins.remove(user)
        try:
            db.session.commit()
        except Exception as exception:
            db.session.rollback()
            current_app.logger.exception(str(exception))
            abort(400)

        # Force send because this could have security implications
        alert_email(
            user,
            "You have been removed as an administator of %s on Staffjoy" %
            organization.name,
            "You have been removed as an organization administrator of the Staffjoy account for %s."
            % organization.name,
            force_send=True)
        return {}, 204

    @permission_org_admin
    @verify_org_admin
    def get(self, org_id, user_id):
        user = User.query.get_or_404(user_id)

        if not user.is_org_admin(org_id):
            return {"message": "user does not exist or is not an admin"}, 404

        response = {
            API_ENVELOPE: marshal(user, user_fields),
            "resources": [],
        }

        return response

    @permission_org_admin
    @verify_org_admin
    def patch(self, org_id, user_id):
        organization = Organization.query.get_or_404(org_id)
        user = User.query.get_or_404(user_id)

        if not user.is_org_admin(org_id):
            return {"message": "user does not exist or is not an admin"}, 404

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
