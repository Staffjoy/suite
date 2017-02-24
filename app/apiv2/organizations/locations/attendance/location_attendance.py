import datetime
import iso8601

from flask import g, current_app, make_response
from flask_restful import marshal, reqparse, Resource, inputs

from app.constants import API_ENVELOPE
from app.helpers import get_default_tz, normalize_to_midnight
from app.models import User, Organization, Location, Role, \
    RoleToUser, Shift2, Timeclock, TimeOffRequest
from app.apiv2.decorators import permission_location_manager, verify_org_location
from app.apiv2.marshal import shift_fields, timeclock_fields, \
    time_off_request_fields

CSV_HEADER = '"Name","Employee Id","Email","Organization","Location","Role","Start time (UTC)","End time (UTC)","Start time (Local timezone - %s)","End time (Local timezone - %s)","Type","Status","Duration (minutes)"'


class LocationAttendanceApi(Resource):
    @verify_org_location
    @permission_location_manager
    def get(self, org_id, location_id):
        """
        returns nested timeclock and shift data for the dates occurring
        between a specified start and end day
        """

        parser = reqparse.RequestParser()
        parser.add_argument("startDate", type=str, required=True)
        parser.add_argument("endDate", type=str, required=True)
        parser.add_argument("csv_export", type=inputs.boolean, default=False)
        parameters = parser.parse_args()

        data = {}
        summary = {}
        iso_date = "%Y-%m-%d"
        default_tz = get_default_tz()

        organization = Organization.query.get(org_id)
        location = Location.query.get(location_id)
        roles = Role.query.filter_by(location_id=location_id).all()

        # get start and end values for the query + ensure good iso formatting
        try:
            start_local = iso8601.parse_date(parameters.get("startDate"))
        except iso8601.ParseError:
            return {
                "message":
                "Start time parameter needs to be in ISO 8601 format"
            }, 400

        try:
            end_local = iso8601.parse_date(parameters.get("endDate"))
        except iso8601.ParseError:
            return {
                "message":
                "End time parameter time needs to be in ISO 8601 format"
            }, 400

        # pytz can't can't have iso8601 utc timezone object (needs naive)
        start_local = normalize_to_midnight(start_local).replace(tzinfo=None)
        end_local = normalize_to_midnight(end_local).replace(tzinfo=None)

        # adjust naive/local times for a utc query
        location_timezone = location.timezone_pytz
        start_utc = location_timezone.localize(start_local).astimezone(
            default_tz)

        # NOTE - the query needs to include the whole last day,
        # so add 1 day ahead and make it a <
        end_utc = normalize_to_midnight(
            (location_timezone.localize(end_local).astimezone(default_tz) +
             datetime.timedelta(days=1, hours=1)
             ).astimezone(location_timezone)).astimezone(default_tz)

        shift_query = Shift2.query \
            .filter(
                Shift2.start >= start_utc,
                Shift2.start < end_utc,
            )

        timeclock_query = Timeclock.query\
            .filter(
                Timeclock.start >= start_utc,
                Timeclock.start < end_utc,
                Timeclock.stop != None
            )

        time_off_request_query = TimeOffRequest.query\
            .filter(
                TimeOffRequest.start >= start_utc,
                TimeOffRequest.start < end_utc,
                TimeOffRequest.state.in_(["approved_paid", "approved_unpaid", "sick"]),
            )

        # determine if csv export
        if parameters.get("csv_export"):

            current_app.logger.info(
                "Generating a timeclock csv export for organization %s location %s"
                % (organization.id, location.id))
            g.current_user.track_event("timeclock_csv_export")

            csv_rows = [CSV_HEADER % (location.timezone, location.timezone)]
            download_name = "attendance-%s-%s-%s.csv" % (
                location.name, parameters.get("startDate"),
                parameters.get("endDate"))

            combined_list = []

            for role in roles:
                for role_to_user in role.members:
                    user_timeclocks = timeclock_query.filter_by(
                        role_id=role.id).filter_by(
                            user_id=role_to_user.user_id).order_by(
                                Timeclock.start.asc()).all()

                    user_time_off_requests = time_off_request_query.filter_by(
                        role_to_user_id=role_to_user.id).order_by(
                            TimeOffRequest.start.asc()).all()

                    combined_list += user_timeclocks + user_time_off_requests

            combined_list.sort(key=lambda x: x.start)

            for record in combined_list:
                start_utc = record.start.isoformat()
                start_local = default_tz.localize(
                    record.start).astimezone(location_timezone).isoformat()
                stop_utc = record.stop.isoformat()
                stop_local = default_tz.localize(
                    record.stop).astimezone(location_timezone).isoformat()

                # record will be either a time off request or a timeclock
                if isinstance(record, Timeclock):
                    rtu = RoleToUser.query.filter_by(
                        role_id=record.role_id, user_id=record.user_id).first()
                    user = User.query.get(record.user_id)
                    role = Role.query.get(record.role_id)
                    minutes = int(
                        (record.stop - record.start).total_seconds() / 60)
                    record_type = "Recorded Time"
                    record_state = ""

                # time off requests
                else:
                    rtu = RoleToUser.query.get(record.role_to_user_id)
                    user = rtu.user
                    role = rtu.role
                    minutes = record.minutes_paid
                    record_type = "Time Off"
                    record_state = record.state.replace("_", " ").title()

                csv_rows.append(
                    ",".join(['"%s"'] * len(CSV_HEADER.split(","))) %
                    (user.name
                     if user.name is not None else "", rtu.internal_id or "",
                     user.email, organization.name, location.name, role.name,
                     start_utc, stop_utc, start_local, stop_local, record_type,
                     record_state, minutes))

            response = make_response("\n".join(csv_rows))
            response.headers[
                "Content-Disposition"] = "attachment; filename=%s" % download_name

            return response

        # create a dict with keys for each day of the week needed
        delta = end_local - start_local
        for x in xrange(delta.days + 1):
            data[(start_local + datetime.timedelta(days=x)
                  ).strftime(iso_date)] = {}

        # all data is nested underneath each role
        for role in roles:

            # Timeclocks and Time Off Requests
            # timeclock and time off request data is nested underneath
            # each user
            for user in role.members:

                role_user_index = str(role.id) + "-" + str(user.user_id)

                # Timeclocks
                user_timeclocks = timeclock_query.filter_by(
                    role_id=role.id).filter_by(user_id=user.user_id).all()

                # sort each timeclock into correct day bucket
                for timeclock in user_timeclocks:

                    # get localized time for placing in the proper bucket
                    localized_dt = default_tz.localize(
                        timeclock.start).astimezone(location_timezone)
                    local_date = localized_dt.strftime(iso_date)
                    elapsed_time = int(
                        (timeclock.stop - timeclock.start).total_seconds())

                    # add timeclock to user object for the right day
                    if role_user_index in data[local_date]:
                        data[local_date][role_user_index]["timeclocks"].append(
                            marshal(timeclock, timeclock_fields))
                        data[local_date][role_user_index][
                            "logged_time"] += elapsed_time

                    # if user has no records on day, create one
                    else:
                        data[local_date][role_user_index] = {
                            "user_id": user.user_id,
                            "role_id": role.id,
                            "timeclocks":
                            [marshal(timeclock, timeclock_fields)],
                            "time_off_requests": None,
                            "shifts": [],
                            "logged_time": elapsed_time,
                        }

                    if role_user_index in summary:
                        summary[role_user_index]["logged_time"] += elapsed_time
                        summary[role_user_index]["timeclock_count"] += 1
                    else:
                        summary[role_user_index] = {
                            "user_id": user.user_id,
                            "role_id": role.id,
                            "logged_time": elapsed_time,
                            "scheduled_time": 0,
                            "shift_count": 0,
                            "timeclock_count": 1,
                            "time_off_request_count": 0,
                        }

                # Time Off Requests
                # user.id is the role_to_user id
                user_time_off_requests = time_off_request_query.filter_by(
                    role_to_user_id=user.id).all()

                for time_off_request in user_time_off_requests:

                    # get localized time for placing in the proper bucket
                    localized_dt = default_tz.localize(
                        time_off_request.start).astimezone(location_timezone)
                    local_date = localized_dt.strftime(iso_date)

                    # convert minutes_paid to seconds
                    recorded_time = time_off_request.minutes_paid * 60

                    # add time_off_request to user object for the right day
                    if role_user_index in data[local_date]:
                        data[local_date][role_user_index][
                            "time_off_requests"] = marshal(
                                time_off_request, time_off_request_fields)
                        data[local_date][role_user_index][
                            "logged_time"] += recorded_time

                    # if user has no records on day, create one
                    else:
                        data[local_date][role_user_index] = {
                            "user_id":
                            user.user_id,
                            "role_id":
                            role.id,
                            "shifts": [],
                            "timeclocks": [],
                            "time_off_requests":
                            marshal(time_off_request, time_off_request_fields),
                            "logged_time":
                            recorded_time,
                        }

                    if role_user_index in summary:
                        summary[role_user_index][
                            "logged_time"] += recorded_time
                        summary[role_user_index]["time_off_request_count"] += 1
                    else:
                        summary[role_user_index] = {
                            "user_id": user.user_id,
                            "role_id": role.id,
                            "logged_time": recorded_time,
                            "scheduled_time": 0,
                            "shift_count": 0,
                            "timeclock_count": 0,
                            "time_off_request_count": 1,
                        }

            # shifts
            shifts = shift_query \
                .filter(
                    Shift2.role_id == role.id,
                    Shift2.user_id > 0,
                ).all()

            # segment out each shift
            for shift in shifts:
                role_user_index = str(shift.role_id) + "-" + str(shift.user_id)

                # get localized time for placing in the proper bucket
                localized_dt = default_tz.localize(
                    shift.start).astimezone(location_timezone)
                local_date = localized_dt.strftime(iso_date)

                # add shift to user object for the right day
                if role_user_index in data[local_date]:
                    data[local_date][role_user_index]["shifts"].append(
                        marshal(shift, shift_fields))

                # if user has no records on day, create one
                else:
                    data[local_date][role_user_index] = {
                        "user_id": shift.user_id,
                        "role_id": role.id,
                        "timeclocks": [],
                        "time_off_requests": None,
                        "shifts": [marshal(shift, shift_fields)],
                    }

                if role_user_index in summary:
                    summary[role_user_index]["shift_count"] += 1
                    summary[role_user_index]["scheduled_time"] += int(
                        (shift.stop - shift.start).total_seconds())
                else:
                    summary[role_user_index] = {
                        "user_id":
                        shift.user_id,
                        "role_id":
                        role.id,
                        "logged_time":
                        0,
                        "scheduled_time":
                        int((shift.stop - shift.start).total_seconds()),
                        "shift_count":
                        1,
                        "timeclock_count":
                        0,
                        "time_off_request_count":
                        0,
                    }

        # remove user index to flatten
        for key in data:
            data[key] = data[key].values()

        return {API_ENVELOPE: data, "summary": summary.values()}
