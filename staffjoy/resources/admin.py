from staffjoy.resource import Resource


class Admin(Resource):
    """Organization administrators"""
    PATH = "organizations/{organization_id}/admins/{user_id}"
    ID_NAME = "user_id"
