import datetime
import iso8601

from flask import g, url_for
from flask_restful import marshal, abort, reqparse, Resource

from app import db
from app.constants import API_ENVELOPE, SECONDS_PER_HOUR
from app.helpers import get_default_tz, check_datetime_is_midnight, \
    normalize_to_midnight
from app.models import TimeOffRequest, Location, RoleToUser, User, Organization
from app.apiv2.decorators import verify_org_location_role_user, \
    permission_location_manager_or_self
from app.apiv2.marshal import time_off_request_fields


class TimeOffRequestsApi(Resource):
    @verify_org_location_role_user
    @permission_location_manager_or_self
    def get(self, org_id, location_id, role_id, user_id):
        """
        returns time off request data for a specific user
        """

        parser = reqparse.RequestParser()
        parser.add_argument("start", type=str)
        parser.add_argument("end", type=str)
        parser.add_argument("state", type=str)
        parameters = parser.parse_args()

        # Filter out null values
        parameters = dict((k, v) for k, v in parameters.iteritems()
                          if v is not None)

        org = Organization.query.get_or_404(org_id)
        location = Location.query.get_or_404(location_id)

        default_tz = get_default_tz()
        local_tz = location.timezone_pytz

        time_off_requests = TimeOffRequest.query \
            .join(RoleToUser) \
            .filter(
                RoleToUser.id == TimeOffRequest.role_to_user_id,
                RoleToUser.user_id == user_id,
                RoleToUser.role_id == role_id
            )

        if "state" in parameters:
            state = None if parameters["state"] == "" else parameters["state"]
            time_off_requests = time_off_requests.filter_by(state=state)

        # check for end 1st
        if "end" in parameters:

            if "start" not in parameters:
                return {
                    "message": "A start parameter must be given with an end."
                }, 400

            # ensure good iso formatting
            try:
                end = iso8601.parse_date(parameters.get("end"))
            except iso8601.ParseError:
                return {
                    "message":
                    "End time parameter time needs to be in ISO 8601 format"
                }, 400
            else:
                end = (end + end.utcoffset()).replace(tzinfo=default_tz)

            time_off_requests = time_off_requests.filter(
                TimeOffRequest.start < end)

        # if a start is defined, it must be iso 8601
        if "start" in parameters:

            # make sure start is in right format, and also convert to full iso form
            try:
                start = iso8601.parse_date(parameters.get("start"))
            except iso8601.ParseError:
                return {
                    "message":
                    "Start time parameter needs to be in ISO 8601 format"
                }, 400
            else:
                start = (start + start.utcoffset()).replace(tzinfo=default_tz)

        # otherwise determine when current week began
        else:
            now = local_tz.localize(datetime.datetime.utcnow())
            start = normalize_to_midnight(
                org.get_week_start_from_datetime(now)).astimezone(default_tz)

        # add start to query
        time_off_requests = time_off_requests.filter(
            TimeOffRequest.start >= start)

        return {
            API_ENVELOPE:
            map(lambda time_off_request: marshal(time_off_request, time_off_request_fields),
                time_off_requests.all())
        }

    @verify_org_location_role_user
    @permission_location_manager_or_self
    def post(self, org_id, location_id, role_id, user_id):
        """
        create a new time off request record
        """

        parser = reqparse.RequestParser()
        parser.add_argument("date", type=str, required=True)
        parser.add_argument("state", type=str)
        parser.add_argument("minutes_paid", type=int, default=0)

        parameters = parser.parse_args()

        # Filter out null values
        parameters = dict((k, v) for k, v in parameters.iteritems()
                          if v is not None)

        org = Organization.query.get(org_id)
        location = Location.query.get(location_id)
        rtu = RoleToUser.query.filter_by(
            role_id=role_id, user_id=user_id, archived=False).first_or_404()
        user = User.query.get(user_id)

        user_name = user.email if user.name is None else user.name

        admin_permissions = g.current_user.is_org_admin_or_location_manager(
            org_id, location_id)
        state = parameters.get("state")

        # verify a valid state
        if state not in [
                None, "approved_paid", "approved_unpaid", "sick", "denied"
        ]:
            return {"message": "Invalid time off request state"}, 400

        # non-admins cannot define a state
        if state is not None and not (admin_permissions or
                                      g.current_user.is_sudo()):
            return {
                "message":
                "Only admins can set a state of 'approved_paid', 'approved_unpaid', 'sick', or 'denied'."
            }, 400

        # extract start and stop dates
        default_tz = get_default_tz()
        local_tz = location.timezone_pytz

        try:
            start = iso8601.parse_date(parameters.get("date"))
        except iso8601.ParseError:
            return {"message": "date needs to be in ISO 8601 format"}, 400
        else:
            # apply any offset (there shouldn't be) and then treat as local time
            start = (start + start.utcoffset()).replace(tzinfo=None)

        start_local = local_tz.localize(start)
        start_utc = start_local.astimezone(default_tz)

        # we are using iso8601 to parse the date, but will be restricting it to only the date
        if not check_datetime_is_midnight(start_local):
            return {
                "message": "date must be at exactly midnight in local time"
            }, 400

        # calculate stop
        stop_local = normalize_to_midnight((start_utc + datetime.timedelta(
            days=1, hours=1)).astimezone(local_tz))
        stop_utc = stop_local.astimezone(default_tz)

        duration_seconds = int((stop_utc - start_utc).total_seconds())

        start_utc = start_utc.replace(tzinfo=None)
        stop_utc = stop_utc.replace(tzinfo=None)

        # to consider daylight savings time, check that the duration between start and stop
        # is between 23 and 25 hours in length
        if not (23 * SECONDS_PER_HOUR <= duration_seconds <= 25 *
                SECONDS_PER_HOUR):
            abort(500)

        # finally check on minutes paid
        # these rules also prevent a non-admin from setting minutes_paid
        minutes_paid = parameters.get("minutes_paid")
        if not (0 <= minutes_paid * 60 <= duration_seconds):
            return {
                "message":
                "Cannot set minutes_paid to be greater than the calendar day"
            }, 400

        if minutes_paid > 0 and state == "approved_unpaid":
            return {
                "message":
                "unpaid time off requests cannot have a minutes_paid greater than 0"
            }, 400

        if minutes_paid == 0 and state == "approved_paid":
            return {
                "message":
                "paid time off requests must have a postitive minutes_paid"
            }, 400

        if state is None and minutes_paid != 0:
            return {
                "message":
                "cannot have minutes_paid greater than 0 for time off requests with an undefined state"
            }, 400

        time_off_request = TimeOffRequest(
            role_to_user_id=rtu.id,
            start=start_utc,
            stop=stop_utc,
            state=state,
            minutes_paid=minutes_paid)

        # managers can create pre-approved time off requests
        if time_off_request.state is not None:
            if admin_permissions:
                time_off_request.approver_user_id = g.current_user.id

        # time off requests cannot overlap
        if time_off_request.has_overlaps():
            return {
                "message":
                "This time off request overlaps with another time off request"
            }, 400

        db.session.add(time_off_request)

        try:
            db.session.commit()
        except:
            abort(500)

        if time_off_request.state in [
                "sick", "approved_paid", "approved_unpaid"
        ]:
            time_off_request.unassign_overlapping_shifts()

        # send an email to managers if a worker is the one making the request
        if not (admin_permissions or g.current_user.is_sudo()):
            display_date = start_local.strftime("%A, %B %-d")

            # subject
            subject = "[Action Required] Time off request for %s on %s" % (
                user_name, display_date)

            # calculate start of current week
            week_start_date = org.get_week_start_from_datetime(
                start_local).strftime("%Y-%m-%d")

            # email body
            message = "%s has requested the day off on %s. Please log in to the Manager to approve or deny it:" % (
                user_name, display_date)

            # construct the url
            manager_url = "%s#locations/%s/scheduling/%s" % (url_for(
                'manager.manager_app', org_id=org_id,
                _external=True), location_id, week_start_date)

            # send it
            location.send_manager_email(subject, message, manager_url)

        g.current_user.track_event("created_time_off_request")
        return marshal(time_off_request, time_off_request_fields), 201
