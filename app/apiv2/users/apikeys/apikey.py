from flask import current_app
from flask_restful import marshal, abort, Resource
from app.apiv2.marshal import api_key_fields

from app import db
from app.constants import API_ENVELOPE
from app.models import ApiKey
from app.apiv2.decorators import permission_self, verify_user_api_key


class ApiKeyApi(Resource):
    method_decorators = [permission_self, verify_user_api_key]

    def get(self, user_id, key_id):
        apikey = ApiKey.query.get(key_id)

        return {API_ENVELOPE: marshal(apikey, api_key_fields)}

    def delete(self, user_id, key_id):
        apikey = ApiKey.query.get(key_id)

        try:
            db.session.delete(apikey)
            db.session.commit()
        except Exception as exception:
            db.session.rollback()
            current_app.logger.exception(str(exception))
            abort(400)

        return {}, 204
