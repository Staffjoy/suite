from flask_restful import marshal, inputs, reqparse, abort, Resource

from app import db
from app.constants import API_ENVELOPE
from app.models import User, Organization, Location

from app.apiv2.decorators import permission_self, permission_sudo
from app.apiv2.helpers import valid_email, user_filter
from app.apiv2.marshal import user_fields, organization_fields, \
    location_fields, role_fields


class UserApi(Resource):
    @permission_self
    def get(self, user_id):

        parser = reqparse.RequestParser()
        parser.add_argument("archived", type=inputs.boolean)
        args = parser.parse_args()
        args = dict((k, v) for k, v in args.iteritems() if v is not None)

        response = {
            API_ENVELOPE: {},
            "resources": ["apikeys", "sessions"],
            "organization_admin": [],
            "role_member": [],
        }
        user = User.query.get_or_404(user_id)

        response[API_ENVELOPE] = marshal(user, user_fields)
        response["organization_admin"] = map(
            lambda organization: marshal(organization, organization_fields),
            user.admin_of.all())

        response["location_manager"] = []
        for location in user.manager_of.all():
            response["location_manager"].append({
                "organization":
                marshal(location.organization, organization_fields),
                "location":
                marshal(location, location_fields),
            })

        # Role admin is a little more tricky because we want to stuff in location and org names + ids

        roles = []
        # Stuff in metadata. BLASPHEMY, I know.
        for assoc in user.roles:

            if "archived" in args:
                if args["archived"] != assoc.archived:
                    continue

            role = marshal(assoc.role, role_fields)

            location = marshal(
                Location.query.get(role["location_id"]), location_fields)
            organization = marshal(
                Organization.query.get(location["organization_id"]),
                organization_fields)

            role["location"] = location
            role["organization"] = organization
            roles.append(role)

        response["role_member"] = roles
        return response

    @permission_sudo
    def patch(self, user_id):
        parser = reqparse.RequestParser()
        parser.add_argument("username", type=str)
        parser.add_argument("name", type=str)
        parser.add_argument("email", type=str)
        parser.add_argument("sudo", type=inputs.boolean)
        parser.add_argument("confirmed", type=inputs.boolean)
        parser.add_argument("active", type=inputs.boolean)
        parser.add_argument("activateReminder", type=inputs.boolean)

        changes = parser.parse_args(strict=True)
        # Filter out null values
        changes = dict((k, v) for k, v in changes.iteritems() if v is not None)
        # Filter some values to lowercase, etc
        changes = dict(
            map(lambda (k, v): (k, user_filter(k, v)), changes.iteritems()))

        user = User.query.get_or_404(user_id)

        # activation email reminder - it can't be committed to this RTU model though
        if "activateReminder" in changes:

            if user.active:
                return {"message": "This user is already active"}, 400

            user.send_activation_reminder(user)
            del changes["activateReminder"]

        if "sudo" in changes.keys():
            allowed = "@staffjoy.com"
            if user.email[-len(allowed):] != allowed:
                abort(400)

        if "email" in changes.keys():
            if not valid_email(changes['email']):
                abort(400)

        for change, value in changes.iteritems():
            if value is not None:
                try:
                    setattr(user, change, value)
                    db.session.commit()
                except:
                    db.session.rollback()
                    abort(400)
        user.flush_associated_shift_caches()
        return changes
