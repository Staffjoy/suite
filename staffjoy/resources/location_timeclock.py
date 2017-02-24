from staffjoy.resource import Resource


class LocationTimeclock(Resource):
    """this is only a get collection endpoint"""
    PATH = "organizations/{organization_id}/locations/{location_id}/timeclocks/"
