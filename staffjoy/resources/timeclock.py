from staffjoy.resource import Resource


class Timeclock(Resource):
    PATH = "organizations/{organization_id}/locations/{location_id}/roles/{role_id}/users/{user_id}/timeclocks/{timeclock_id}"
    ID_NAME = "timeclock_id"
