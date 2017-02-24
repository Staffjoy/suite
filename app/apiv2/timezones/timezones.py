from flask_restful import Resource
from app.constants import API_ENVELOPE

import pytz


class TimezonesApi(Resource):
    # Pseudo-public
    def get(self):
        """gets all known timezones"""

        return {
            API_ENVELOPE:
            map(lambda timezone: {"name": timezone}, pytz.all_timezones)
        }
