from flask import current_app
from flask_restful import marshal, abort, reqparse, Resource

from app import db
from app.constants import API_ENVELOPE
from app.models import User, Organization
from app.apiv2.decorators import permission_org_admin
from app.apiv2.marshal import user_fields
from app.apiv2.email import alert_email


class OrgAdminsApi(Resource):
    @permission_org_admin
    def get(self, org_id):
        """ List all admins in this organization """
        response = {
            API_ENVELOPE: [],
        }

        org = Organization.query.get_or_404(org_id)
        response[API_ENVELOPE] = map(lambda admin: marshal(admin, user_fields),
                                     org.admins.all())

        return response

    @permission_org_admin
    def post(self, org_id):
        """ Add a user as an admin either by user id or email """
        parser = reqparse.RequestParser()
        parser.add_argument("email", type=str)
        parser.add_argument("id", type=int)
        parser.add_argument("name", type=str)
        parameters = parser.parse_args(strict=True)

        organization = Organization.query.get_or_404(org_id)

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

        if user.is_org_admin(org_id):
            return {"message": "user already an admin"}, 400

        organization.admins.append(user)
        try:
            db.session.commit()
        except Exception as exception:
            db.session.rollback()
            current_app.logger.exception(str(exception))
            abort(400)

        alert_email(
            user, "You have been added as an adminstator of %s on Staffjoy" %
            organization.name,
            "You have been added as an organization administrator of the Staffjoy account for %s."
            % organization.name)

        return marshal(user, user_fields), 201
