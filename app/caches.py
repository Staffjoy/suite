import json
import os
import binascii
from datetime import datetime

from flask import current_app, request

from app import cache


class BaseCache():
    KEY = "%s"
    EXPIRY = 1209600  # Two weeks in seconds

    @classmethod  # Use class method instead of static so we can access constants
    def get(cls, cache_id=""):
        results = cache.get(cls.KEY % cache_id)
        if results is None:
            return None

        try:
            return json.loads(results)
        except:
            current_app.logger.warning(
                "Corrupted cache - returned invalid json for %s %s. Purging cache. Returned body was %s."
                % (type(cls).__name__, cache_id, results))
            cls.delete(cache_id)
            return None  # cache miss

    @classmethod
    def set(cls, cache_id, result):
        cache.set(
            cls.KEY % cache_id,
            json.dumps(result), )
        # Expire the cache - we don't want to crowd Redis with every
        # single old schedule ever created! Only fresh ones.
        cache.expire(cls.KEY % cache_id, cls.EXPIRY)

    @classmethod
    def lock(cls, cache_id, result=True):
        """Like set, but fails and returns false if already set"""
        success = cache.setnx(
            cls.KEY % cache_id,
            json.dumps(result), )
        if success:
            cache.expire(cls.KEY % cache_id, cls.EXPIRY)
        return success

    @classmethod
    def delete(cls, cache_id):
        cache.delete(cls.KEY % cache_id)

    @classmethod
    def get_key_count(cls):
        """Number of active keys - used for API"""
        return len(cache.keys(cls.KEY % "*"))

    @classmethod
    def delete_all(cls):
        """Delete all matching items"""
        # Method - get all keys using wildcard search,
        # then delete key by key.
        redis_keys = cache.keys(cls.KEY % "*")
        for key in redis_keys:
            cache.delete(key)

        current_app.logger.info("Flushed %s keys for %s" %
                                (len(redis_keys), cls.__name__))

    @classmethod
    def get_all_keys(cls):
        """Get all matching keys - for debug purposes"""
        # Method - get all keys using wildcard search,
        # then delete key by key.
        return cache.keys(cls.KEY % "*")


class ShiftsCache(BaseCache):
    KEY = "shifts-from-schedule-id-%s"


class SchedulesCache(BaseCache):
    # TODO deprecate with APIv1 destruction / deprecation
    KEY = "schedules-from-role-id-%s"


class Schedules2Cache(BaseCache):
    KEY = "shifts2-from-schedule-id-%s"


class Shifts2Cache(BaseCache):
    KEY = "schedules2-from-role-id-%s"


class ScheduleMessagesCache(BaseCache):
    KEY = "messages-from-schedule-id-%s"


class TimezonesCache(BaseCache):
    KEY = "timezones%s"


class PeopleScheduledPerWeekCache(BaseCache):
    KEY = "people-scheduled-week-%s"
    EXPIRY = 24 * 60 * 60  # One day in seconds


class RoleToUserCache(BaseCache):
    """
    caches the user_id and role_id associated with a role_to_user_id
    in order to assist with mapping
    """

    KEY = "role-to-user-%s"
    EXPIRY = 60 * 60 * 24 * 30  # 3 months in seconds


class IncidentCache(BaseCache):
    KEY = "incident-%s"  # Do not pass a string
    EXPIRY = 15 * 60  # Fifteen minutes in seconds. Cron job should clear it.


class PhoneVerificationCache(BaseCache):
    KEY = "phone-verification-user_id-%s"
    EXPIRY = 60 * 60  # 1 hour in seconds


class SessionCache(BaseCache):
    """Cache sessions in the database so that we can force a logout"""

    KEY = "session-%(user_id)s-%(session_id)s"
    KEY_LENGTH = 3  # hex input - strlen will be double

    @classmethod
    def create_session(cls, user_id, expiration=3600):
        """Create a session for a user that expires and return session_id"""
        session_id = binascii.hexlify(os.urandom(cls.KEY_LENGTH))

        # Set value to "last used" time - we can use this in the future :-)
        cache.set(cls.KEY % {"user_id": user_id,
                             "session_id": session_id}, cls._session_info())

        # Expire the cache - we don't want to crowd Redis with every
        # single old schedule ever created! Only fresh ones.
        cache.expire(cls.KEY % {"user_id": user_id,
                                "session_id": session_id}, expiration)
        return session_id

    @classmethod
    def validate_session(cls, user_id, session_id):
        """Validate that the user can log in. Records request data!"""
        results = cache.get(cls.KEY %
                            {"user_id": user_id,
                             "session_id": session_id})
        if results is None:
            return False

        # Set last used time to now
        cache.set(cls.KEY % {"user_id": user_id,
                             "session_id": session_id}, cls._session_info())
        return True

    @classmethod
    def delete_session(cls, user_id, session_id):
        cache.delete(cls.KEY % {"user_id": user_id, "session_id": session_id})

    @classmethod
    def get_session_info(cls, user_id, session_id):
        results = cache.get(cls.KEY %
                            {"user_id": user_id,
                             "session_id": session_id})
        if results is None:
            return {}

        try:
            return json.loads(results)
        except:
            current_app.logger.warning(
                "Corrupted session info - returned invalid json")
            # Do not delete session becuase it's not worth logging the user out, and we overwrite
            return None  # cache miss

    @classmethod
    def get_all_sessions(cls, user_id):
        redis_keys = cache.keys(cls.KEY %
                                {"user_id": user_id,
                                 "session_id": "*"})
        keys = []

        # We need to chop off the beginning of the redis key to get session id
        base_key_length = len(cls.KEY % {"user_id": user_id, "session_id": ""})
        for redis_key in redis_keys:
            keys.append(redis_key[base_key_length:])

        return keys

    @classmethod
    def delete_all_sessions(cls, user_id):
        keys = cls.get_all_sessions(user_id)
        for key in keys:
            cache.delete(cls.KEY % {"user_id": user_id, "session_id": key})

    @classmethod
    def _session_info(cls):
        """Info we store when a session is used"""
        return json.dumps({
            "remote_ip":
            request.headers.get("CF-Connecting-IP", request.remote_addr),
            "last_used":
            datetime.utcnow().isoformat(),
        })


class BillingEventsCache(BaseCache):
    """A lock for preventing actions on duplicate events"""
    KEY = "billing-event-%s"
    # Hypothetically duplicates sent weeks apart will cause issues, but that's ok
    EXPIRY = 1209600  # Two weeks in seconds


class CronTimeclockNotificationSmsCache(BaseCache):
    """A lock for preventing actions on duplicate events"""
    KEY = "cron-timeclock-notification-sms-%s"
    # Hypothetically duplicates sent weeks apart will cause issues, but that's ok
    EXPIRY = 300  # 5 minutes in seconds (bc of search window)
