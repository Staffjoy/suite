from flask import current_app

from app.caches import BaseCache

from datetime import datetime, timedelta
import iso8601


class BaseNotificationLimiter(BaseCache):
    """
    A base class for using cache as a notification limiter.
    Needs a KEY, EXPIRY time, NAME, and optionally WRITE_LOG
    and COMPARE_LAST_SEEN
    """

    # Toggle this for whether to check the user's last seen time
    # when determining whether we're allowed to send
    COMPARE_LAST_SEEN = True

    # how this notification shows up in logs
    NAME = "Base Notifier"

    WRITE_LOG = True

    @classmethod
    def allowed_to_send(cls, user):
        """
        determines if a notification is able to be sent
        """

        try:
            last_reminder = cls.get(user.id)
            last_reminder = iso8601.parse_date(last_reminder).replace(
                tzinfo=None)
        except:
            last_reminder = None

        if not last_reminder:
            return True

        if cls.COMPARE_LAST_SEEN:
            # Still allowed to send if user has been active
            # since last notification.
            if user.last_seen > last_reminder:
                cls.delete(user.id)
                return True

        # redis doesn't guarantee that the key isn't expired exactly at expiration time
        # check if it *should* have been expired
        if last_reminder + timedelta(seconds=cls.EXPIRY) < datetime.utcnow():
            cls.delete(user.id)
            return True

        if cls.WRITE_LOG:
            current_app.logger.info(
                "Not sending %s notification to user %s because it was sent recently"
                % (cls.NAME, user.id))
            return False

    @classmethod
    def mark_sent(cls, user):
        """marks a notification as sent"""
        cls.set(user.id, datetime.utcnow().isoformat())


class UserActivationReminderLimiter(BaseNotificationLimiter):
    """Limits the amount of activation emails a user can receive in a time span"""

    KEY = "notification-activation-reminder-%s"
    EXPIRY = 3600
    NAME = "activation reminder"


class ShiftChangeNotificationLimiter(BaseNotificationLimiter):
    """Limits how often a user can be emailed about changed shifts"""
    KEY = "notification-shift-change-%s"
    EXPIRY = 1200  # 20 minutes
    NAME = "shift change"


class AvailableShiftsNotificationLimiter(BaseNotificationLimiter):
    """Limits how often a user can be emailed about claimable shifts"""
    KEY = "notification-shift-available-%s"
    EXPIRY = 21600  # 6 hours
    NAME = "shift available"


class PingLimiter(BaseNotificationLimiter):
    """Limits how often the database and Intercom get notified about a user being active"""
    NAME = "database and intercom ping"
    COMPARE_LAST_SEEN = False
    WRITE_LOG = False
    KEY = "ping-%s"
    EXPIRY = 60  # 1 minute
