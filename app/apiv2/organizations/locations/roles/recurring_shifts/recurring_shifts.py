from flask import g, current_app
from flask_restful import marshal, abort, reqparse, Resource

from app import constants, db
from app.models import RecurringShift, RoleToUser
from app.apiv2.decorators import verify_org_location_role, \
    permission_location_member, permission_location_manager
from app.apiv2.marshal import recurring_shift_fields


class RecurringShiftsApi(Resource):
    @verify_org_location_role
    @permission_location_member
    def get(self, org_id, location_id, role_id):
        """
        get recurring shifts for a role. can optionally filter by user_id
        """

        parser = reqparse.RequestParser()
        parser.add_argument("user_id", type=int)
        parameters = parser.parse_args()

        # Filter out null values
        parameters = dict((k, v) for k, v in parameters.iteritems()
                          if v is not None)

        recurring_shifts_query = RecurringShift.query.filter_by(
            role_id=role_id)

        if "user_id" in parameters:
            user_id = None if parameters[
                "user_id"] == constants.UNASSIGNED_USER_ID else parameters[
                    "user_id"]

            recurring_shifts_query = recurring_shifts_query.filter_by(
                user_id=user_id)

        return {
            constants.API_ENVELOPE:
            map(lambda recurring_shift: marshal(recurring_shift, recurring_shift_fields),
                recurring_shifts_query.all())
        }

    @verify_org_location_role
    @permission_location_manager
    def post(self, org_id, location_id, role_id):
        """
        create a new recurring shift
        """

        parser = reqparse.RequestParser()
        parser.add_argument("start_day", type=str, required=True)
        parser.add_argument("start_hour", type=int, required=True)
        parser.add_argument("start_minute", type=int, required=True)
        parser.add_argument("duration_minutes", type=int, required=True)
        parser.add_argument("user_id", type=int, default=0)
        parser.add_argument("quantity", type=int, default=1)
        parameters = parser.parse_args()

        start_day = parameters.get("start_day").lower()
        start_hour = parameters.get("start_hour")
        start_minute = parameters.get("start_minute")
        duration_minutes = parameters.get("duration_minutes")
        user_id = parameters.get("user_id")
        quantity = parameters.get("quantity")

        if start_day not in constants.DAYS_OF_WEEK:
            return {
                "message": "start_day must be a day of the week e.g. 'monday'."
            }, 400

        if not (0 <= start_hour < constants.DAY_LENGTH):
            return {
                "message":
                "start_hour must be between 0 and %s." % constants.DAY_LENGTH
            }, 400

        if not (0 <= start_minute < constants.MINUTES_PER_HOUR):
            return {
                "message":
                "start_minute must be between 0 and %s." %
                constants.MINUTES_PER_HOUR
            }, 400

        if not (1 <= duration_minutes <= constants.MAX_SHIFT_LENGTH_MINUTES):
            return {
                "message":
                "duration_minutes must be between 1 and " +
                constants.MAX_SHIFT_LENGTH_MINUTES
            }, 400

        # user_id needs to be None in database
        if user_id == constants.UNASSIGNED_USER_ID:
            user_id = None

        else:
            # verify active user in the role
            rtu = RoleToUser.query.filter_by(
                role_id=role_id, user_id=user_id, archived=False).first()

            if rtu is None:
                return {"message": "Worker does not belong to this role"}, 400

        if not (1 <= quantity < constants.RECURRING_SHIFT_MAX_QUANTITY):
            return {
                "message":
                "quantity must be between 1 and %s" %
                constants.RECURRING_SHIFT_MAX_QUANTITY
            }, 400

        if user_id is not None and quantity > 1:
            return {
                "message":
                "Recurring shifts can only be of quantity 1 when being assigned to workers"
            }, 400

        recurring_shift = RecurringShift(
            role_id=role_id,
            user_id=user_id,
            start_day=start_day,
            start_hour=start_hour,
            start_minute=start_minute,
            duration_minutes=duration_minutes,
            quantity=quantity)

        if user_id > 0:
            if recurring_shift.has_overlaps():
                return {
                    "message":
                    "This recurring shift overlaps with an existing one"
                }, 400

        db.session.add(recurring_shift)
        try:
            db.session.commit()
        except:
            abort(500)

        g.current_user.track_event("created_recurring_shift")
        current_app.logger.info("Recurring shift %s created" %
                                recurring_shift.id)

        return marshal(recurring_shift, recurring_shift_fields), 201
