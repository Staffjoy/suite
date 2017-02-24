import iso8601
from flask import g, make_response
from flask_restful import marshal, abort, reqparse, Resource, inputs

from app.constants import MAX_SHIFT_LENGTH, SECONDS_PER_HOUR, API_ENVELOPE
from app.helpers import get_default_tz
from app.models import User, Location, Role, RoleToUser, Schedule2, Shift2
from app.caches import Shifts2Cache
from app import db
from app.apiv2.decorators import verify_org_location_role, \
    permission_location_member, permission_location_manager
from app.apiv2.marshal import shift_fields
from app.apiv2.email import alert_changed_shift, alert_available_shifts


class ShiftsApi(Resource):
    CSV_HEADER = '"name","position","start date","end date","start time","finish time","notes","title","open"'

    @verify_org_location_role
    @permission_location_member
    def get(self, org_id, location_id, role_id):
        # NOTE - we always include user's name with shifts. This helps the front-end.

        parser = reqparse.RequestParser()
        parser.add_argument("start", type=str, required=True)
        parser.add_argument("end", type=str, required=True)
        parser.add_argument("user_id", type=int)
        parser.add_argument("csv_export", type=inputs.boolean, default=False)
        parser.add_argument(
            "include_summary", type=inputs.boolean, default=False)
        parser.add_argument(
            "filter_by_published", type=inputs.boolean, default=False)
        parameters = parser.parse_args(
        )  # Strict breaks calls from parent methods? Sigh.

        # Filter out null values
        parameters = dict((k, v) for k, v in parameters.iteritems()
                          if v is not None)

        default_tz = get_default_tz()

        shifts = Shift2.query.filter_by(role_id=role_id)

        # start and end must be supplied - check if in ok format
        try:
            start = iso8601.parse_date(parameters.get("start"))
        except iso8601.ParseError:
            return {
                "message":
                "Start time parameter needs to be in ISO 8601 format"
            }, 400
        else:
            start = (start + start.utcoffset()).replace(tzinfo=default_tz)

        try:
            end = iso8601.parse_date(parameters.get("end"))
        except iso8601.ParseError:
            return {
                "message":
                "End time parameter time needs to be in ISO 8601 format"
            }, 400
        else:
            end = (end + end.utcoffset()).replace(tzinfo=default_tz)

        shifts = shifts \
            .filter(
                Shift2.start < end,
                Shift2.start >= start,
            )

        if "user_id" in parameters:
            user_id_value = parameters["user_id"]
            if user_id_value == 0:
                user_id_value = None

            shifts = shifts.filter_by(user_id=user_id_value)

        # filter by only published shifts
        if parameters.get("filter_by_published"):
            shifts = shifts.filter_by(published=True)

        # now execute the query
        shifts = shifts \
            .order_by(
                Shift2.start.asc(),
            ) \
            .all()

        # determine if csv export
        if parameters.get("csv_export"):

            csv_rows = [self.CSV_HEADER]

            role_name = Role.query.get_or_404(role_id).name
            download_name = "shifts-%s-%s-%s.csv" % (role_name, start, end)

            for shift in shifts:
                if shift.user_id is None:
                    user_name = "Unassigned Shift"
                    shift_status = "open"
                else:
                    user = User.query.get_or_404(shift.user_id)

                    user_name = user.name if user.name else user.email
                    shift_status = "closed"

                start_date = shift.start.strftime("%-m/%-d/%y")
                start_time = shift.start.strftime("%-I%p")
                stop_date = shift.stop.strftime("%-m/%-d/%y")
                stop_time = shift.stop.strftime("%-I%p")
                open_value = 1 if shift_status == "open" else ""

                csv_rows.append('"%s","%s","%s","%s","%s","%s","","%s","%s"' %
                                (user_name, role_name, start_date, stop_date,
                                 start_time, stop_time, shift_status,
                                 open_value))

            response = make_response("\n".join(csv_rows))
            response.headers[
                "Content-Disposition"] = "attachment; filename=%s" % download_name

            return response

        output = {
            API_ENVELOPE:
            map(lambda shift: marshal(shift, shift_fields), shifts)
        }

        if parameters.get("include_summary"):
            users_summary = {}

            for shift in shifts:
                user_id = shift.user_id if shift.user_id else 0

                if user_id in users_summary.keys():
                    users_summary[user_id]["shifts"] += 1
                    users_summary[user_id]["minutes"] += int(
                        (shift.stop - shift.start).total_seconds() / 60)
                else:
                    if user_id == 0:
                        name = "Unassigned shifts"
                    else:
                        user = User.query.get_or_404(shift.user_id)
                        name = user.name if user.name else user.email

                    users_summary[user_id] = {
                        "user_id":
                        user_id,
                        "user_name":
                        name,
                        "shifts":
                        1,
                        "minutes":
                        int((shift.stop - shift.start).total_seconds() / 60)
                    }

            output["summary"] = users_summary.values()

        return output

    @verify_org_location_role
    @permission_location_manager
    def post(self, org_id, location_id, role_id):
        """
        create a new shift
        """

        parser = reqparse.RequestParser()
        parser.add_argument("start", type=str, required=True)
        parser.add_argument("stop", type=str, required=True)
        parser.add_argument("user_id", type=int)
        parser.add_argument("published", type=inputs.boolean)
        parser.add_argument("description", type=str)
        parameters = parser.parse_args()

        # Filter out null values
        parameters = dict((k, v) for k, v in parameters.iteritems()
                          if v is not None)

        default_tz = get_default_tz()
        local_tz = Location.query.get(location_id).timezone_pytz

        # start time
        try:
            start = iso8601.parse_date(parameters.get("start"))
        except iso8601.ParseError:
            return {
                "message": "Start time needs to be in ISO 8601 format"
            }, 400
        else:
            start = (start + start.utcoffset()).replace(tzinfo=default_tz)

        # stop time
        try:
            stop = iso8601.parse_date(parameters.get("stop"))
        except iso8601.ParseError:
            return {"message": "Stop time needs to be in ISO 8601 format"}, 400
        else:
            stop = (stop + stop.utcoffset()).replace(tzinfo=default_tz)

        # stop can't be before start
        if start >= stop:
            return {"message": "Stop time must be after start time"}, 400

        # shifts are limited to 23 hours in length
        if int((stop - start).total_seconds()) > MAX_SHIFT_LENGTH:
            return {
                "message":
                "Shifts cannot be more than %s hours long" %
                (MAX_SHIFT_LENGTH / SECONDS_PER_HOUR)
            }, 400

        shift = Shift2(
            role_id=role_id,
            start=start,
            stop=stop,
            published=parameters.get("published", False))

        if "description" in parameters:
            description = parameters.get("description")

            if len(description) > Shift2.MAX_DESCRIPTION_LENGTH:
                return {
                    "message":
                    "Description cannot me more than %s characters" %
                    Shift2.MAX_DESCRIPTION_LENGTH
                }, 400

            shift.description = description

        user_id = parameters.get("user_id")

        # if user_id defined, and if not for unassigned shift, check if user is in role
        # and make sure it won't overlap with existing shifts
        if user_id is not None:
            if user_id > 0:
                role_to_user = RoleToUser.query.filter_by(
                    user_id=user_id, role_id=role_id, archived=False).first()

                if role_to_user is None:
                    return {
                        "message":
                        "User does not exist or is not apart of role"
                    }, 400

                # check if this shift can be assigned to the user
                shift.user_id = user_id

                if shift.has_overlaps():
                    return {
                        "message": "This shift overlaps with an existing shift"
                    }, 400

        db.session.add(shift)
        try:
            db.session.commit()
        except:
            abort(500)

        g.current_user.track_event("created_shift")

        # check if a schedule exists during this time - if so, bust the cache
        schedule = Schedule2.query \
            .filter(
                Schedule2.role_id == role_id,
                Schedule2.start <= shift.start,
                Schedule2.stop > shift.start,
            ).first()

        if schedule is not None:
            Shifts2Cache.delete(schedule.id)

        # timezone stuff
        local_datetime = default_tz.localize(shift.start).astimezone(local_tz)

        # only send emails if future and published
        if not shift.is_in_past and shift.published:

            # if shift is unassigned - alert people that it's available
            if shift.user_id is None:

                # get all users who are eligible for the shift
                eligible_users, _ = shift.eligible_users()

                alert_available_shifts(org_id, location_id, role_id,
                                       local_datetime, eligible_users)

            # Otherwise send an alert_changed_shift notification
            # (function has logic for whether to send)
            elif (g.current_user.id != shift.user_id):
                alert_changed_shift(org_id, location_id, role_id,
                                    local_datetime, shift.user_id)

        return marshal(shift, shift_fields), 201
