from flask_restful import Resource

from app.constants import API_ENVELOPE, PLAN_PUBLIC_KEYS
from app.plans import plans


class PlansApi(Resource):
    # Public (for authenticated users)
    def get(self):
        # Flatten dict to an array to match rest of api style
        output = []
        for plan_id, value in plans.iteritems():
            clean_plan = {"id": plan_id}
            for key in PLAN_PUBLIC_KEYS:
                clean_plan[key] = value.get(key)

            output.append(clean_plan)

        return {
            API_ENVELOPE: output,
        }
