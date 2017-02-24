from flask_restful import abort, Resource

from app.constants import API_ENVELOPE
from app.plans import plans
from app.constants import PLAN_PUBLIC_KEYS


class PlanApi(Resource):
    # Any authenticated users can access
    def get(self, plan_id):
        if plan_id not in plans.keys():
            abort(404)

        plan_data = plans[plan_id]
        clean_plan = {"id": plan_id}
        for key in PLAN_PUBLIC_KEYS:
            clean_plan[key] = plan_data.get(key)

        return {
            API_ENVELOPE: clean_plan,
        }
