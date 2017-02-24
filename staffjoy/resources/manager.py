from staffjoy.resource import Resource


class Manager(Resource):
    """Location managers"""
    PATH = "organizations/{organization_id}/locations/{location_id}/managers/{user_id}"
    ID_NAME = "user_id"
