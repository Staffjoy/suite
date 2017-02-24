from flask_restful import Resource
from app.constants import API_ENVELOPE
from app.models import User
from app.apiv2.decorators import permission_self


class SessionsApi(Resource):
    @permission_self
    def get(self, user_id):
        user = User.query.get_or_404(user_id)
        data = user.get_all_sessions()
        for key in data.keys():
            data[key]["key"] = key

        return {API_ENVELOPE: data.values()}, 200

    @permission_self
    def delete(self, user_id):
        user = User.query.get_or_404(user_id)
        user.logout_all_sessions()
        return {}, 204
