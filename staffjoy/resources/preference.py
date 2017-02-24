from staffjoy.resource import Resource


class Preference(Resource):
    PATH = "organizations/{organization_id}/locations/{location_id}/roles/{role_id}/schedules/{schedule_id}/preferences/{user_id}"
    ID_NAME = "user_id"
