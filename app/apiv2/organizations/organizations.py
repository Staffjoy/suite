from flask_restful import marshal, abort, reqparse, Resource

from app import db
from app.constants import API_ENVELOPE, DAYS_OF_WEEK
from app.models import Organization
from app.apiv2.decorators import permission_sudo
from app.apiv2.marshal import organization_fields


class OrganizationsApi(Resource):
    @permission_sudo
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument("offset", type=int, default=0)
        parser.add_argument("limit", type=int, default=25)

        args = parser.parse_args()

        offset = args["offset"]
        limit = args["limit"]

        response = {
            "offset": offset,
            "limit": limit,
            API_ENVELOPE: [],
        }

        organizations = Organization.query
        response[API_ENVELOPE] = map(
            lambda organization: marshal(organization, organization_fields),
            organizations.limit(limit).offset(offset).all())

        return response

    @permission_sudo
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument("name", type=str)
        parser.add_argument("day_week_starts", type=str, default="monday")
        parser.add_argument("plan", type=str, default="flex-v1")
        parser.add_argument("trial_days", type=int, default=14)
        parameters = parser.parse_args(strict=True)

        if parameters.get("day_week_starts") not in DAYS_OF_WEEK:
            return {"message": "day_week_starts is not valid"}, 400

        if parameters.get("trial_days") < 0:
            return {"messages": "trial_days cannot be less than 0"}

        o = Organization(
            name=parameters.get("name"),
            day_week_starts=parameters.get("day_week_starts"),
            trial_days=parameters.get("trial_days"))
        db.session.add(o)
        try:
            db.session.commit()
            return marshal(o, organization_fields), 201
        except:
            abort(500)
