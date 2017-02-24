import datetime
from copy import deepcopy

import iso8601
from flask import g, current_app
from flask_restful import marshal, abort, reqparse, Resource, inputs

from app import db
from app.constants import API_ENVELOPE, MAX_TIMECLOCK_HOURS, SECONDS_PER_HOUR
from app.models import Timeclock, User
from app.apiv2.decorators import verify_org_location_role_user_timeclock, \
    permission_location_manager_or_self, permission_location_manager
from app.apiv2.marshal import timeclock_fields
from app.apiv2.email import alert_timeclock_change


class TimeclockApi(Resource):
    @verify_org_location_role_user_timeclock
    @permission_location_manager_or_self
    def get(self, org_id, location_id, role_id, user_id, timeclock_id):
        """
        returns a specific timeclock record
        """

        timeclock = Timeclock.query.get_or_404(timeclock_id)

        return {
            API_ENVELOPE: marshal(timeclock, timeclock_fields),
            "resources": [],
        }

    @verify_org_location_role_user_timeclock
    @permission_location_manager_or_self
    def patch(self, org_id, location_id, role_id, user_id, timeclock_id):
        """
        modifies an existing timeclock record
        """

        parser = reqparse.RequestParser()
        parser.add_argument("start", type=str)
        parser.add_argument("stop", type=str)
        parser.add_argument("close", type=inputs.boolean)
        parameters = parser.parse_args()

        # Filter out null values
        parameters = dict((k, v) for k, v in parameters.iteritems()
                          if v is not None)
        changes = {}

        timeclock = Timeclock.query.get_or_404(timeclock_id)
        user = User.query.get(user_id)

        original_start = timeclock.start
        original_stop = timeclock.stop

        admin_permissions = g.current_user.is_sudo(
        ) or g.current_user.is_org_admin_or_location_manager(org_id,
                                                             location_id)

        if "close" in parameters and ("start" in parameters or
                                      "stop" in parameters):
            return {
                "message": "Cannot have start/end with a close parameter"
            }, 400

        if not admin_permissions:
            if set(("close", )) != set(parameters):
                return {
                    "message": "You are only allowed to close the timeclock."
                }, 400

        # get new or current start value
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
            start = timeclock.start

        # get new or current stop value
        if "stop" in parameters:
            try:
                stop = iso8601.parse_date(parameters.get("stop"))
            except iso8601.ParseError:
                return {
                    "message": "Stop time needs to be in ISO 8601 format"
                }, 400
            else:
                stop = (stop + stop.utcoffset()).replace(tzinfo=None)
        else:
            stop = timeclock.stop

        # end timeclock at existing time - must be only parameter defined
        if "close" in parameters:
            if set(("close", )) != set(parameters):
                return {
                    "message":
                    "Can not close timeclock with other parameters defined - please remove them from the request"
                }, 400

            if stop is not None:
                return {
                    "message": "This timeclock has already been closed"
                }, 400

            changes["stop"] = datetime.datetime.utcnow().isoformat()

        # stop still might be none, but if not, need to do some validation
        if stop is not None:

            # start must be before stop
            if start >= stop:
                return {"message": "Start time must be before stop time"}, 400

            # doesn't exceed max length
            if int(
                (stop - start
                 ).total_seconds()) > MAX_TIMECLOCK_HOURS * SECONDS_PER_HOUR:
                return {
                    "message":
                    "Timeclocks cannot be more than %s hours long" %
                    MAX_TIMECLOCK_HOURS
                }, 400

            timeclock_copy = deepcopy(timeclock)
            timeclock_copy.start = start
            timeclock_copy.stop = stop

            if timeclock_copy.has_overlaps():
                return {
                    "message": "Timeclock overlaps with other timeclocks"
                }, 400

            # cannot modify a timeclock and make it in the future
            utcnow = datetime.datetime.utcnow()
            if stop > utcnow:
                return {
                    "message": "Cannot adjust a timeclock to the future"
                }, 400

        if "start" in parameters:
            changes["start"] = start.isoformat()

        if "stop" in parameters:
            changes["stop"] = stop.isoformat()

        for change, value in changes.iteritems():
            try:
                setattr(timeclock, change, value)
                db.session.commit()
            except Exception as exception:
                db.session.rollback()
                current_app.logger.exception(str(exception))
                abort(400)

        if "close" in parameters:
            g.current_user.track_event("timeclock_stop")
        else:
            g.current_user.track_event("timeclock_modified")

        # always send an email if it's someone else's timeclock
        if timeclock.user_id != g.current_user.id:
            alert_timeclock_change(timeclock, org_id, location_id, role_id,
                                   original_start, original_stop, user,
                                   g.current_user)

        return changes

    @verify_org_location_role_user_timeclock
    @permission_location_manager
    def delete(self, org_id, location_id, role_id, user_id, timeclock_id):
        """
        deletes a timeclock record
        """

        timeclock = Timeclock.query.get_or_404(timeclock_id)
        user = User.query.get_or_404(user_id)
        original_start = timeclock.start
        original_stop = timeclock.stop

        try:
            db.session.delete(timeclock)
            db.session.commit()
        except Exception as exception:
            db.session.rollback()
            current_app.logger.error(str(exception))
            abort(400)

        if timeclock.user_id != g.current_user.id:
            alert_timeclock_change(None, org_id, location_id, role_id,
                                   original_start, original_stop, user,
                                   g.current_user)

        g.current_user.track_event("timeclock_deleted")
        return {}, 204
