from flask_restful import marshal, abort, Resource
from sqlalchemy import asc

from app.constants import API_ENVELOPE
from app.models import Schedule2, Role, Location, Organization
from app.apiv2.decorators import permission_sudo
from app.apiv2.marshal import tasking_schedule_fields


class ChompTasksApi(Resource):
    method_decorators = [permission_sudo]

    def get(self):
        """ Return all queued calculations """
        response = {}
        response[API_ENVELOPE] = {}

        for state in ['chomp-queue', 'chomp-processing']:
            data = Schedule2.query.join(Role)\
                .join(Location)\
                .join(Organization)\
                .filter(Schedule2.state == state, Organization.active == True)\
                .all()
            response[API_ENVELOPE][state] = map(
                lambda schedule: marshal(schedule, tasking_schedule_fields),
                data)

        return response

    def post(self):
        """ Assign a scheduling task """
        s = Schedule2.query\
            .join(Role)\
            .join(Location)\
            .join(Organization)\
            .filter(Schedule2.state == "chomp-queue", Organization.active == True)\
            .order_by(asc(Schedule2.last_update))\
            .first()

        if s is None:
            abort(404)

        s.transition_to_chomp_processing()

        role = Role.query.get(s.role_id)
        loc = Location.query.get(role.location_id)

        return {
            "schedule_id": s.id,
            "role_id": role.id,
            "location_id": loc.id,
            "organization_id": loc.organization_id,
        }
