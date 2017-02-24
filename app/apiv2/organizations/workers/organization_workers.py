from flask_restful import inputs, reqparse, Resource
from sqlalchemy import select

from app import db
from app.constants import API_ENVELOPE
from app.models import Location, Role, RoleToUser, User
from app.apiv2.decorators import permission_org_member


class OrganizationWorkersApi(Resource):
    @permission_org_member
    def get(self, org_id):

        parser = reqparse.RequestParser()
        parser.add_argument("archived", type=inputs.boolean)
        parser.add_argument("filter_by_email", type=str)
        parser.add_argument("filter_by_location_id", type=int)
        parser.add_argument("filter_by_role_id", type=int)
        args = parser.parse_args()
        args = dict((k, v) for k, v in args.iteritems() if v is not None)

        workers_query = select([User.email, User.name, Location.id, Location.name, Role.id, Role.name, RoleToUser.user_id, RoleToUser.archived]) \
            .where(RoleToUser.user_id == User.id) \
            .where(RoleToUser.role_id == Role.id) \
            .where(Role.location_id == Location.id) \
            .where(Location.organization_id == org_id) \
            .select_from(User) \
            .select_from(RoleToUser) \
            .select_from(Role) \
            .select_from(Location)

        if "archived" in args:
            workers_query = workers_query.where(
                RoleToUser.archived == args["archived"])

        if "filter_by_location_id" in args:
            workers_query = workers_query.where(
                Location.id == args["filter_by_location_id"])

        if "filter_by_role_id" in args:
            workers_query = workers_query.where(
                Role.id == args["filter_by_role_id"])

        if "filter_by_email" in args:
            workers_query = workers_query.where(
                User.email == args["filter_by_email"])

        workers = db.session.execute(workers_query).fetchall()

        result = []
        for worker in workers:
            result.append({
                "email": worker[0],
                "name": worker[1],
                "location_id": worker[2],
                "location_name": worker[3],
                "role_id": worker[4],
                "role_name": worker[5],
                "user_id": worker[6],
                "archived": worker[7],
            })

        return {
            API_ENVELOPE: result,
        }
