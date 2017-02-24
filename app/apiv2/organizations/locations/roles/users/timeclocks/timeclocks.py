import datetime

import iso8601
from flask import g
from flask_restful import marshal, abort, reqparse, Resource, inputs

from app import constants, db
from app.helpers import get_default_tz, normalize_to_midnight
from app.models import Timeclock, Location, Organization
from app.apiv2.decorators import verify_org_location_role_user, \
    permission_location_manager_or_self
from app.apiv2.marshal import timeclock_fields


class TimeclocksApi(Resource):
    @verify_org_location_role_user
    @permission_location_manager_or_self
    def get(self, org_id, location_id, role_id, user_id):
        """
        returns timeclock data for a specific user
        """

        parser = reqparse.RequestParser()
        parser.add_argument("active", type=inputs.boolean)
        parser.add_argument("start", type=str)
        parser.add_argument("end", type=str)
        parameters = parser.parse_args()

        # Filter out null values
        parameters = dict((k, v) for k, v in parameters.iteritems()
                          if v is not None)

        org = Organization.query.get_or_404(org_id)
        location = Location.query.get_or_404(location_id)

        default_tz = get_default_tz()
        local_tz = location.timezone_pytz

        timeclocks = Timeclock.query \
            .filter_by(role_id=role_id) \
            .filter_by(user_id=user_id)

        # if searching for active timeclocks, do not include start and end query ranges
        if "active" in parameters:
            timeclocks = timeclocks.filter_by(stop=None)

        # start and end query
        else:

            # check for end 1st
            if "end" in parameters:

                if "start" not in parameters:
                    return {
                        "message":
                        "A start parameter must be given with an end."
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

                timeclocks = timeclocks.filter(Timeclock.start < end)

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
                    start = (start + start.utcoffset()).replace(
                        tzinfo=default_tz)

            # otherwise determine when current week began
            else:
                now = local_tz.localize(datetime.datetime.utcnow())
                start = normalize_to_midnight(
                    org.get_week_start_from_datetime(now)).astimezone(
                        default_tz)

            # add start to query
            timeclocks = timeclocks.filter(Timeclock.start >= start)

        return {
            constants.API_ENVELOPE:
            map(lambda timeclock: marshal(timeclock, timeclock_fields),
                timeclocks.all())
        }

    @verify_org_location_role_user
    @permission_location_manager_or_self
    def post(self, org_id, location_id, role_id, user_id):
        """
        create a new timeclock record
        """

        parser = reqparse.RequestParser()
        parser.add_argument("start", type=str)
        parser.add_argument("stop", type=str)
        parameters = parser.parse_args()

        # Filter out null values
        parameters = dict((k, v) for k, v in parameters.iteritems()
                          if v is not None)

        admin_permissions = g.current_user.is_sudo(
        ) or g.current_user.is_org_admin_or_location_manager(org_id,
                                                             location_id)
        stop = None
        utcnow = datetime.datetime.utcnow()

        # check if user already has a timeclock open
        existing_open_timeclocks = Timeclock.query \
            .filter_by(role_id=role_id) \
            .filter_by(user_id=user_id) \
            .filter_by(stop=None) \
            .all()

        # a regular worker is not allowed to assign start/stop times
        if not admin_permissions:
            if any(parameters.get(x) for x in ["start", "stop"]):
                return {
                    "message":
                    "You do not have permission to set a specific start or stop time, please remove them from the request."
                }, 400

        # do validation if parameters were supplied
        if "start" in parameters:
            try:
                start = iso8601.parse_date(parameters.get("start"))
            except iso8601.ParseError:
                return {
                    "message": "Start time needs to be in ISO 8601 format"
                }, 400
            else:
                start = (start + start.utcoffset()).replace(tzinfo=None)

        else:
            start = datetime.datetime.utcnow()

        if "stop" in parameters:

            # must have a start if stop is provided
            if parameters.get("start") is None:
                return {
                    "message": "A start time must be provided with a stop"
                }, 400

            try:
                stop = iso8601.parse_date(parameters.get("stop"))
            except iso8601.ParseError:
                return {
                    "message": "Stop time needs to be in ISO 8601 format"
                }, 400
            else:
                stop = (stop + stop.utcoffset()).replace(tzinfo=None)

            # stop can't be before start
            if start >= stop:
                return {"message": "Stop time must be after start time"}, 400

            # check that its within allowed length
            if int((stop - start).total_seconds(
            )) > constants.MAX_TIMECLOCK_HOURS * constants.SECONDS_PER_HOUR:
                return {
                    "message":
                    "Timeclocks cannot be more than %s hours long" %
                    constants.MAX_TIMECLOCK_HOURS
                }, 400

        # this allows a manager to create past timeclock records, but will
        # prevent them from accidentally clocking in multiple times. if stop is
        # not None, it means a start and stop time have been defined and validated
        if stop is None:
            if len(existing_open_timeclocks) > 0:
                return {
                    "message":
                    "You are currently clocked into a different timeclock."
                }, 400

        # cannot create a timeclock in the future
        else:
            if (start > utcnow) or (stop > utcnow):
                return {
                    "message": "Cannot create a timeclock in the future"
                }, 400

        timeclock = Timeclock(
            role_id=role_id, user_id=user_id, start=start, stop=stop)

        # if the timeclock is being opened, don't check for an overlap
        # if a manager is creating a timeclock, check for an overlap
        if stop is not None:
            if timeclock.has_overlaps():
                return {
                    "message": "Timeclock overlaps with other timeclocks"
                }, 400

        db.session.add(timeclock)

        try:
            db.session.commit()
        except:
            abort(500)

        g.current_user.track_event("timeclock_start")
        return marshal(timeclock, timeclock_fields), 201
