from flask_restful import marshal, abort, Resource

from app.models import Schedule2
from app.apiv2.decorators import permission_sudo
from app.apiv2.marshal import tasking_schedule_fields


class MobiusTaskApi(Resource):
    method_decorators = [permission_sudo]

    def get(self, schedule_id):
        """ Peek at a schedule """
        s = Schedule2.query.get_or_404(schedule_id)

        return marshal(s, tasking_schedule_fields)

    def delete(self, schedule_id):
        """ Mark a task as done """
        s = Schedule2.query.get_or_404(schedule_id)
        if s.state != "mobius-processing":
            abort(400)

        s.transition_to_published()
        return "{}", 204
