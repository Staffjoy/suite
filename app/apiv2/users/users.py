from flask_restful import marshal, reqparse, abort, Resource

from app.constants import API_ENVELOPE
from app.models import User

from app.apiv2.decorators import permission_sudo
from app.apiv2.helpers import valid_email
from app.apiv2.marshal import user_fields


class UsersApi(Resource):
    @permission_sudo
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument("offset", type=int, default=0)
        parser.add_argument("limit", type=int, default=25)
        # Search
        parser.add_argument("filterByUsername", type=str, required=False)
        parser.add_argument("filterByEmail", type=str, required=False)

        args = parser.parse_args()

        offset = args["offset"]
        limit = args["limit"]
        filterByUsername = args["filterByUsername"]
        filterByEmail = args["filterByEmail"]

        response = {
            "offset": offset,
            "limit": limit,
            API_ENVELOPE: [],
            "filters": {
                "filterByUsername": filterByUsername,
                "filterByEmail": filterByEmail,
            },
        }

        users = User.query

        if filterByEmail is not None:
            users = users.filter(User.email.like(filterByEmail.lower()))

        if filterByUsername is not None:
            users = users.filter(User.username.like(filterByUsername.lower()))

        response[API_ENVELOPE] = map(lambda user: marshal(user, user_fields),
                                     users.limit(limit).offset(offset).all())

        return response

    @permission_sudo
    def post(self):
        """Invites a user to join as the user authenticated against the API """
        parser = reqparse.RequestParser()
        parser.add_argument("name", type=str)
        parser.add_argument("email", type=str, required=True)
        parameters = parser.parse_args(strict=True)

        if not valid_email(parameters['email']):
            abort(400)

        u = User.create_and_invite(parameters['email'], parameters['name'])

        return marshal(u, user_fields), 201
