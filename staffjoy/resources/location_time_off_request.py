from staffjoy.resource import Resource


class LocationTimeOffRequest(Resource):
    """this is only a get collection endpoint"""
    PATH = "organizations/{organization_id}/locations/{location_id}/timeoffrequests/"
