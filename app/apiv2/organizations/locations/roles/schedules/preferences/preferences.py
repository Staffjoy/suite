import json

from flask import g
from flask.ext import restful
from flask_restful import marshal, abort

from app import db
from app.constants import API_ENVELOPE
from app.models import Preference, Role
from app.apiv2.decorators import verify_org_location_role_schedule, \
    permission_location_manager, permission_location_manager_or_self, \
    schedule_preference_modifiable
from app.apiv2.marshal import preference_fields
from app.apiv2.helpers import verify_days_of_week_struct


class PreferencesApi(restful.Resource):
    @verify_org_location_role_schedule
    @permission_location_manager
    def get(self, org_id, location_id, role_id, schedule_id):
        response = {
            API_ENVELOPE: [],
        }

        preferences = Preference.query.filter_by(schedule_id=schedule_id).all()
        response[API_ENVELOPE] = map(
            lambda preference: marshal(preference, preference_fields),
            preferences)

        return response

    @verify_org_location_role_schedule
    @permission_location_manager_or_self
    @schedule_preference_modifiable
    def post(self, org_id, location_id, role_id, schedule_id):
        parser = restful.reqparse.RequestParser()
        parser.add_argument("user_id", type=int, required=True)
        parser.add_argument("preference", type=str, required=True)
        parameters = parser.parse_args(strict=True)

        # Check and see if there is existing preference
        p = Preference.query.filter(
            Preference.user_id == parameters.get("user_id"),
            Preference.schedule_id == schedule_id).first()

        if p is not None:
            return {
                "message":
                "User already has preference - use a patch method to modify it."
            }, 400

        try:
            preference = json.loads(parameters.get("preference"))
        except:
            return {"message": "Unable to parse preference json body"}, 400
        if preference is None:
            return {"message": "Unable to parse preference json body"}, 400
        if not verify_days_of_week_struct(preference, True):
            return {"message": "preference is improperly formatted"}, 400

        user_id = parameters.get("user_id")

        # verify user_id is valid to add
        assocs = Role.query.get(role_id).members
        ok = False
        for assoc in assocs:
            if user_id == assoc.user_id:
                ok = True
        if not ok:
            return {"message": "User not in role"}, 400

        p = Preference(
            preference=json.dumps(preference),
            user_id=user_id,
            schedule_id=schedule_id, )

        db.session.add(p)
        try:
            db.session.commit()
            g.current_user.track_event("created_preference")
            return marshal(p, preference_fields), 201
        except:
            abort(500)
