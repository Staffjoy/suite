from staffjoy.resource import Resource


class TimeOffRequest(Resource):
    PATH = "organizations/{organization_id}/locations/{location_id}/roles/{role_id}/users/{user_id}/timeoffrequests/{time_off_request_id}"
    ID_NAME = "time_off_request_id"
