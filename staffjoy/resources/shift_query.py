from staffjoy.resource import Resource


class ShiftQuery(Resource):
    """Returns workers that can claim a potential shift"""
    PATH = "organizations/{organization_id}/locations/{location_id}/roles/{role_id}/shiftquery/"
