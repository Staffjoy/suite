from flask.ext import restful
from app.constants import API_ENVELOPE
from app.models import User
from app.apiv2.decorators import permission_self


class SessionApi(restful.Resource):
    @permission_self
    def get(self, user_id, session_id):
        user = User.query.get(user_id)
        result = user.get_target_session(session_id)
        result.update({"key": session_id})

        return {API_ENVELOPE: result}, 200

    @permission_self
    def delete(self, user_id, session_id):
        user = User.query.get_or_404(user_id)
        user.logout_target_session(session_id)
        return {}, 204
