from staffjoy.resource import Resource


class ShiftEligibleWorker(Resource):
    """Returns workers that can claim a given shift"""
    PATH = "organizations/{organization_id}/locations/{location_id}/roles/{role_id}/shifts/{shift_id}/users/{user_id}"
    ID_NAME = "user_id"
