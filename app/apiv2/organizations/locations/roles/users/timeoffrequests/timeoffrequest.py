import datetime

from flask import g, current_app, url_for
from flask_restful import marshal, abort, reqparse, Resource

from app import db
from app.constants import API_ENVELOPE
from app.helpers import get_default_tz
from app.models import TimeOffRequest, User, Location, RoleToUser, Organization
from app.apiv2.decorators import permission_location_manager, \
    verify_org_location_role_user_time_off_request, \
    permission_location_manager_or_self
from app.apiv2.marshal import time_off_request_fields
from app.apiv2.email import alert_email


class TimeOffRequestApi(Resource):
    @verify_org_location_role_user_time_off_request
    @permission_location_manager_or_self
    def get(self, org_id, location_id, role_id, user_id, time_off_request_id):
        """
        returns a specific time off request record
        """

        time_off_request = TimeOffRequest.query.get_or_404(time_off_request_id)

        return {
            API_ENVELOPE: marshal(time_off_request, time_off_request_fields),
            "resources": [],
        }

    @verify_org_location_role_user_time_off_request
    @permission_location_manager
    def patch(self, org_id, location_id, role_id, user_id,
              time_off_request_id):
        """
        modifies an existing time_off_request record
        NOTE that start and stop cannot be modified
        """

        parser = reqparse.RequestParser()
        parser.add_argument("state", type=str)
        parser.add_argument("minutes_paid", type=int)

        parameters = parser.parse_args()

        # Filter out null values
        parameters = dict((k, v) for k, v in parameters.iteritems()
                          if v is not None)
        changes = {}

        time_off_request = TimeOffRequest.query.get_or_404(time_off_request_id)
        role_to_user = RoleToUser.query.get(time_off_request.role_to_user_id)
        user = User.query.get(user_id)
        location = Location.query.get(location_id)
        org = Organization.query.get(org_id)

        # verify for state
        state = parameters.get("state", time_off_request.state)

        if state not in [
                None, "", "approved_paid", "approved_unpaid", "sick", "denied"
        ]:
            return {"message": "Invalid time off request state"}, 400

        if "state" in parameters:
            # state can be set to None - which get parsed through as an empty string
            if not parameters["state"]:
                changes["state"] = None
                changes["approver_user_id"] = None
            else:
                changes["state"] = parameters["state"]

                # log the approver if its an administrator
                if g.current_user.is_org_admin_or_location_manager(
                        org_id, location_id):
                    changes["approver_user_id"] = g.current_user.id
                else:
                    changes["approver_user_id"] = None

        # verification for minutes_paid
        minutes_paid = parameters.get("minutes_paid",
                                      time_off_request.minutes_paid)
        duration = int(
            (time_off_request.stop - time_off_request.start).total_seconds())

        if not (0 <= minutes_paid * 60 <= duration):
            return {
                "message":
                "minutes_paid must be within the duration of the day"
            }, 400

        if minutes_paid > 0 and state == "approved_unpaid":
            return {
                "message":
                "Unpaid time off requests cannot have a minutes_paid greater than 0"
            }, 400

        if minutes_paid == 0 and state == "approved_paid":
            return {
                "message":
                "Paid time off requests must have a postitive minutes_paid"
            }, 400

        if state is None and minutes_paid != 0:
            return {
                "message":
                "Cannot have minutes_paid greater than 0 for time off requests with an undefined state"
            }, 400

        if "minutes_paid" in parameters:
            changes["minutes_paid"] = parameters["minutes_paid"]

        for change, value in changes.iteritems():
            try:
                setattr(time_off_request, change, value)
                db.session.commit()
            except Exception as exception:
                db.session.rollback()
                current_app.logger.exception(str(exception))
                abort(400)

        g.current_user.track_event("time_off_request_modified")

        # unassign shifts that overlap
        if changes.get("state") is not None and time_off_request.state in [
                "sick", "approved_paid", "approved_unpaid"
        ]:
            time_off_request.unassign_overlapping_shifts()

        # send an email to the user whenever the approved state changes
        # only send an email for unarchived workers and
        # the time off request is in the future
        if changes.get("state") is not None \
            and not role_to_user.archived \
            and time_off_request.start > datetime.datetime.utcnow():

            default_tz = get_default_tz()
            local_tz = location.timezone_pytz

            start_local = default_tz.localize(
                time_off_request.start).astimezone(local_tz)
            display_date = start_local.strftime("%A, %B %-d")

            # calculate myschedules url
            week_start_date = org.get_week_start_from_datetime(
                start_local).strftime("%Y-%m-%d")

            myschedules_url = "%s#week/%s" % (url_for(
                'myschedules.myschedules_app',
                org_id=org_id,
                location_id=location_id,
                role_id=role_id,
                user_id=user_id,
                _external=True), week_start_date)

            # prepare subject and starting body - each state can be fine tuned
            if time_off_request.state == "denied":
                subject = "Your time off request on %s has been denied" % display_date
                body = "Your time off request on %s has been denied" % display_date

            elif time_off_request.state == "approved_paid":
                subject = "Your time off request on %s has been approved" % display_date
                body = "You have been approved for paid time off on %s" % display_date

            elif time_off_request.state == "approved_unpaid":
                subject = "Your time off request on %s has been approved" % display_date
                body = "You have been approved for unpaid time off on %s" % display_date

            elif time_off_request.state == "sick":
                subject = "Your time off request on %s has been approved" % display_date
                body = "You have been approved to take a sick day on %s" % display_date

            # add in approval info if it is avilable
            if time_off_request.approver_user_id:
                approval_user = User.query.get(
                    time_off_request.approver_user_id)
                approval_name = approval_user.email if approval_user.name is None else approval_user.email
                body += " by %s." % approval_name
            else:
                body += "."

            body += " Visit My Schedules to learn more:<br><a href=\"%s\">%s</a>" % (
                myschedules_url, myschedules_url)

            alert_email(user, subject, body)

        return changes

    @verify_org_location_role_user_time_off_request
    @permission_location_manager_or_self
    def delete(self, org_id, location_id, role_id, user_id,
               time_off_request_id):
        """
        deletes a time_off_request record
        """

        time_off_request = TimeOffRequest.query.get_or_404(time_off_request_id)

        admin_permissions = g.current_user.is_sudo(
        ) or g.current_user.is_org_admin_or_location_manager(org_id,
                                                             location_id)

        # workers can delete a time off request if it has not been approved/rejected by manager
        if (time_off_request.state is not None and not admin_permissions):
            abort(401)

        try:
            db.session.delete(time_off_request)
            db.session.commit()
        except Exception as exception:
            db.session.rollback()
            current_app.logger.error(str(exception))
            abort(400)

        g.current_user.track_event("time_off_request_deleted")
        return {}, 204
