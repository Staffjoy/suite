from staffjoy.resource import Resource


class RecurringShift(Resource):
    PATH = "organizations/{organization_id}/locations/{location_id}/roles/{role_id}/recurringshifts/{recurring_shift_id}"
    ID_NAME = "recurring_shift_id"
