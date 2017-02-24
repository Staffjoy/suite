from flask_restful import marshal, reqparse, Resource

from app.apiv2.marshal import api_key_fields

from app.constants import API_ENVELOPE
from app.models import ApiKey

from app.apiv2.decorators import permission_self


class ApiKeysApi(Resource):
    method_decorators = [permission_self]

    def get(self, user_id):
        apikeys = ApiKey.query.filter_by(user_id=user_id).all()
        return {
            API_ENVELOPE:
            map(lambda apikey: marshal(apikey, api_key_fields), apikeys)
        }

    def post(self, user_id):
        parser = reqparse.RequestParser()
        parser.add_argument("name", type=str, required=True)
        parameters = parser.parse_args(strict=True)

        # This function handles all the db logic
        plaintext_key = ApiKey.generate_key(user_id, parameters.get("name"))

        # NOTE - this is the ONLY time the key will be in plaintext
        return {"key": plaintext_key}
