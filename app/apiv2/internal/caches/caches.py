from flask import current_app, g
from flask_restful import Resource

from app.caches import BaseCache
from app.constants import API_ENVELOPE
from app.apiv2.decorators import permission_sudo


class CachesApi(Resource):
    method_decorators = [permission_sudo]

    def get(self):
        """Return number of keys in redis"""
        return {API_ENVELOPE: {"active_keys": BaseCache.get_key_count()}}

    def delete(self):
        """Flush aaaal the caches """
        BaseCache.delete_all()
        current_app.logger.info("User %s flushed all caches through API" %
                                g.current_user.id)
        return "{}", 204
