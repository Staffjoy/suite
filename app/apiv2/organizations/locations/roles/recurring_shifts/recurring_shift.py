from copy import deepcopy

from flask import g, current_app
from flask_restful import marshal, abort, reqparse, Resource

from app import db
from app import constants
from app.models import RecurringShift, RoleToUser
from app.apiv2.decorators import verify_org_location_role_recurring_shift, \
    permission_location_member, permission_location_manager
from app.apiv2.marshal import recurring_shift_fields


class RecurringShiftApi(Resource):
    @verify_org_location_role_recurring_shift
    @permission_location_member
    def get(self, org_id, location_id, role_id, recurring_shift_id):
        """
        get a specific recurring shift
        """

        recurring_shift = RecurringShift.query.get_or_404(recurring_shift_id)
        return {
            constants.API_ENVELOPE:
            marshal(recurring_shift, recurring_shift_fields),
            "resources": [],
        }

    @verify_org_location_role_recurring_shift
    @permission_location_manager
    def patch(self, org_id, location_id, role_id, recurring_shift_id):
        """
        modify a recurring shift
        """

        parser = reqparse.RequestParser()
        parser.add_argument("start_day", type=str)
        parser.add_argument("start_hour", type=int)
        parser.add_argument("start_minute", type=int)
        parser.add_argument("duration_minutes", type=int)
        parser.add_argument("user_id", type=int)
        parser.add_argument("quantity", type=int)
        changes = parser.parse_args()

        # Filter out null values
        changes = dict((k, v) for k, v in changes.iteritems() if v is not None)

        recurring_shift = RecurringShift.query.get_or_404(recurring_shift_id)

        start_day = changes.get("start_day", recurring_shift.start_day).lower()
        start_hour = changes.get("start_hour", recurring_shift.start_hour)
        start_minute = changes.get("start_minute",
                                   recurring_shift.start_minute)
        duration_minutes = changes.get("duration_minutes",
                                       recurring_shift.duration_minutes)
        user_id = changes.get("user_id", recurring_shift.user_id)
        quantity = changes.get("quantity", recurring_shift.quantity)

        # user_id needs to be 0 -> None in database
        if user_id == constants.UNASSIGNED_USER_ID:
            user_id = None

        if changes.get("user_id") == constants.UNASSIGNED_USER_ID:
            changes["user_id"] = None

        if start_day not in constants.DAYS_OF_WEEK:
            return {
                "message": "start_day must be a day of the week e.g. 'monday'."
            }, 400

        if not (0 <= start_hour < constants.DAY_LENGTH):
            return {"message": "start_hour must be between 0 and 23."}, 400

        if not (0 <= start_minute < constants.MINUTES_PER_HOUR):
            return {"message": "start_minute must be between 0 and 59."}, 400

        if not (1 <= duration_minutes <= constants.MAX_SHIFT_LENGTH_MINUTES):
            return {
                "message":
                "duration_minutes must be between 1 and " +
                constants.MAX_SHIFT_LENGTH_MINUTES
            }, 400

        if user_id is not None:
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

        if user_id is not None:
            if quantity > 1:
                return {
                    "message":
                    "Recurring shifts can only be of quantity 1 when being assigned to workers"
                }, 400

            # check for overlap against a copy
            recurring_shift_copy = deepcopy(recurring_shift)
            recurring_shift_copy.user_id = user_id
            recurring_shift_copy.start_day = start_day
            recurring_shift_copy.start_hour = start_hour
            recurring_shift_copy.start_minute = start_minute
            recurring_shift_copy.duration_minutes = duration_minutes

            if recurring_shift_copy.has_overlaps():
                return {
                    "message":
                    "Recurring shift overlaps with an existing recurring shift"
                }, 400

        for change, value in changes.iteritems():
            try:
                setattr(recurring_shift, change, value)
                db.session.commit()
            except Exception as exception:
                db.session.rollback()
                current_app.logger.exception(str(exception))
                abort(400)

        g.current_user.track_event("modified_recurring_shift")
        current_app.logger.info("Recurring shift %s modified" %
                                recurring_shift_id)

        return changes

    @verify_org_location_role_recurring_shift
    @permission_location_manager
    def delete(self, org_id, location_id, role_id, recurring_shift_id):
        """
        delete a recurring shift
        """

        recurring_shift = RecurringShift.query.get_or_404(recurring_shift_id)

        # store for logging use after deleting
        start_day = recurring_shift.start_day
        start_hour = recurring_shift.start_hour
        start_minute = recurring_shift.start_minute

        try:
            db.session.delete(recurring_shift)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(str(e))
            abort(500)

        current_app.logger.info(
            "Deleted recurring shift on %s starting at %s:%s" %
            (start_day, start_hour, start_minute))

        return {}, 204
