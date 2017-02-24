from staffjoy.resource import Resource


class ApiKey(Resource):
    """User session"""
    PATH = "users/{user_id}/apikeys/{apikey_id}"
    ID_NAME = "apikey_id"
