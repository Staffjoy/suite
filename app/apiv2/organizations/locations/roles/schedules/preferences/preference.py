import json

from flask import g, current_app
from flask_restful import marshal, abort, reqparse, Resource

from app import db
from app.constants import API_ENVELOPE
from app.models import Preference
from app.apiv2.decorators import verify_org_location_role_schedule, \
    permission_location_manager_or_self, schedule_preference_modifiable, \
    permission_location_manager
from app.apiv2.marshal import preference_fields
from app.apiv2.helpers import verify_days_of_week_struct


class PreferenceApi(Resource):
    @verify_org_location_role_schedule
    @permission_location_manager_or_self
    def get(self, org_id, location_id, role_id, schedule_id, user_id):
        p = Preference.query.filter(
            Preference.user_id == user_id,
            Preference.schedule_id == schedule_id).first()

        if p is None:
            abort(404)

        return {API_ENVELOPE: marshal(p, preference_fields)}

    @verify_org_location_role_schedule
    @permission_location_manager_or_self
    @schedule_preference_modifiable
    def patch(self, org_id, location_id, role_id, schedule_id, user_id):
        parser = reqparse.RequestParser()
        parser.add_argument("preference", type=str, required=True)
        changes = parser.parse_args(strict=True)

        # Filter out null values
        changes = dict((k, v) for k, v in changes.iteritems() if v is not None)
        p = Preference.query.filter(
            Preference.user_id == user_id,
            Preference.schedule_id == schedule_id).first()

        if p is None:
            abort(404)

        if changes.get("preference") is not None:
            try:
                preference = json.loads(changes.get("preference"))
            except:
                return {"message": "Unable to parse preference json body"}, 400
            if preference is None:
                return {"message": "Unable to parse preference json body"}, 400
            if not verify_days_of_week_struct(preference, True):
                return {"message": "preference is improperly formatted"}, 400

            changes["preference"] = preference

        for change, value in changes.iteritems():
            if change == "preference":
                value = json.dumps(value)

            if value is not None:
                try:
                    setattr(p, change, value)
                    db.session.commit()
                except Exception as exception:
                    db.session.rollback()
                    current_app.logger.exception(str(exception))
                    abort(400)

        g.current_user.track_event("updated_preference")
        return changes

    @verify_org_location_role_schedule
    @permission_location_manager
    @schedule_preference_modifiable
    def delete(self, org_id, location_id, role_id, schedule_id, user_id):
        p = Preference.query.filter(
            Preference.user_id == user_id,
            Preference.schedule_id == schedule_id).first()

        if p is None:
            abort(404)

        try:
            db.session.delete(p)
            db.session.commit()
        except Exception as exception:
            db.session.rollback()
            current_app.logger.error(str(exception))
            abort(400)

        g.current_user.track_event("deleted_preference")
        return {}, 204
