from staffjoy.resource import Resource


class Session(Resource):
    """User session"""
    PATH = "users/{user_id}/sessions/{session_id}"
    ID_NAME = "session_id"
