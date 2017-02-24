from flask import g
from flask_restful import marshal, Resource

from app.constants import API_ENVELOPE
from app.models import Shift2
from app.apiv2.decorators import verify_org_location_role_shift, \
    permission_location_manager
from app.apiv2.marshal import user_fields


class ShiftEligibleUsersApi(Resource):
    @verify_org_location_role_shift
    @permission_location_manager
    def get(self, org_id, location_id, role_id, shift_id):
        shift = Shift2.query.get(shift_id)
        allow_past = g.current_user.is_sudo(
        ) or g.current_user.is_org_admin_or_location_manager(org_id,
                                                             location_id)

        within_caps, exceeds_caps = shift.get_all_eligible_users(
            allow_past=allow_past)

        marshal_within_caps = map(lambda user: marshal(user, user_fields),
                                  within_caps)
        marshal_exceeds_caps = map(lambda user: marshal(user, user_fields),
                                   exceeds_caps)

        for user in marshal_within_caps:
            user["within_caps"] = True

        for user in marshal_exceeds_caps:
            user["within_caps"] = False

        return {API_ENVELOPE: marshal_within_caps + marshal_exceeds_caps}
