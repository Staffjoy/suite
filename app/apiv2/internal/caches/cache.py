from flask import current_app, g, abort
from flask_restful import Resource

from app.apiv2.decorators import permission_sudo
from app.caches import ShiftsCache, SchedulesCache, Schedules2Cache, \
    Shifts2Cache, IncidentCache, SessionCache
from app.constants import API_ENVELOPE

KEY_TO_CACHES = {
    "shifts": [ShiftsCache, Shifts2Cache],
    "schedules": [SchedulesCache, Schedules2Cache],
    "incidents": [IncidentCache],
    "sessions": [SessionCache]
}


class CacheApi(Resource):
    method_decorators = [permission_sudo]

    def get(self, cache_key):
        """View number of active keys in cache"""
        if cache_key not in KEY_TO_CACHES.keys():
            abort(404)

        count = 0
        for cache in KEY_TO_CACHES[cache_key]:
            count += cache.get_key_count()

        return {API_ENVELOPE: {"active_keys": count}}

    def delete(self, cache_key):
        """Flush target cache"""
        if cache_key not in KEY_TO_CACHES.keys():
            abort(404)

        for cache in KEY_TO_CACHES[cache_key]:
            cache.delete_all()

        current_app.logger.info("User %s flushed the %s cache through API" %
                                (g.current_user.id, cache_key))

        return {}, 204
