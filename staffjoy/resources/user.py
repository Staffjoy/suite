from staffjoy.resource import Resource
from staffjoy.resources.session import Session
from staffjoy.resources.apikey import ApiKey


class User(Resource):
    PATH = "users/{user_id}"
    ID_NAME = "user_id"

    def get_sessions(self):
        return Session.get_all(parent=self)

    def get_session(self, id):
        return Session.get(parent=self, id=id)

    def get_apikeys(self):
        return ApiKey.get_all(parent=self)

    def get_apikey(self, id):
        return ApiKey.get(parent=self, id=id)

    def create_apikey(self, **kwargs):
        return ApiKey.create(parent=self, **kwargs)
