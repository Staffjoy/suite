from staffjoy.resource import Resource


class LocationShift(Resource):
    """this is only a get collection endpoint"""
    PATH = "organizations/{organization_id}/locations/{location_id}/shifts/"
