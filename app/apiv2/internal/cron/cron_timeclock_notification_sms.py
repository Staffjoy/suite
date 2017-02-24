from datetime import datetime, timedelta

from flask import current_app
from sqlalchemy.sql import and_

from app.models import RoleToUser, User, Timeclock, Role, Shift2
from app.caches import CronTimeclockNotificationSmsCache

# Margin of error. Allows one skipped cron.
SEARCH_WINDOW_MINUTES = 2


def run_cron_timeclock_notification_sms():
    """Register functions to run here"""
    _alert_time_to_clock_in()
    _alert_time_to_clock_out()

    # Alert for 3 hours of lateness
    for t in [1, 2, 3]:
        _alert_late_clock_out(hours_offset=t)


def _query_base():
    """Get RoleToUsers for this type of notification"""
    # filters to add on:
    # - a timeclock join (think - inner or outer join!?)
    # - timeclock start time
    # - timeclock stop time
    # - shift start time
    # - shift stop time

    # TODO - filter by plan in the future

    return RoleToUser.query\
        .join(User,
            and_(
                RoleToUser.user_id == User.id,
            )
        )\
        .join(Role,
            and_(
                RoleToUser.role_id == Role.id,
            )
        )\
        .join(Shift2,
            and_(
                Shift2.user_id == RoleToUser.user_id,
            )
        )\
        .filter(
            RoleToUser.archived == False,
            User.phone_national_number != None,
            User.phone_country_code != None,
            User.enable_timeclock_notification_sms == True,
            User.active == True,
            Role.enable_timeclock == True,
        )


def _alert_time_to_clock_in():
    """Alert users to clock in if they have not"""
    KEY = "alert-time-to-clock-in-%s"

    now = datetime.utcnow()

    role_to_user_models = _query_base()\
        .outerjoin(Timeclock,
            and_(
                Timeclock.role_id == Role.id,
                Timeclock.start != None,
                Timeclock.stop == None,
                Timeclock.user_id == User.id,
            )
        )\
        .filter(
            # It's start of shift
            Shift2.start <= now,
            Shift2.start >= (now - timedelta(minutes=SEARCH_WINDOW_MINUTES)),
            Shift2.stop > now,
            # And user is not clocked in
            Timeclock.id == None,
        )\
        .all()

    for rtu in role_to_user_models:
        # Use role to user id instead of user - multiple roles!
        if CronTimeclockNotificationSmsCache.lock(KEY % rtu.id):
            user = rtu.user
            user.send_sms("Hi %s - your shift just started. Clock in here: %s"
                          % (user.first_name, current_app.config.get("URL")))


def _alert_time_to_clock_out():
    """Alert users to clock out if they have not at end of shift"""
    KEY = "alert-time-to-clock-out-%s"

    now = datetime.utcnow()

    role_to_user_models = _query_base()\
        .join(Timeclock,
            and_(
                Timeclock.role_id == Role.id,
                Timeclock.start != None,
                Timeclock.stop == None,
                Timeclock.user_id == User.id,
            )
        )\
        .filter(
            # It's end of shift
            Shift2.stop <= now,
            Shift2.stop >= (now - timedelta(minutes=SEARCH_WINDOW_MINUTES)),
        )\
        .all()

    for rtu in role_to_user_models:
        # Use role to user id instead of user - multiple roles!
        if CronTimeclockNotificationSmsCache.lock((KEY % rtu.id)):
            user = rtu.user
            user.send_sms("Hi %s - your shift just ended. Clock out here: %s" %
                          (user.first_name, current_app.config.get("URL")))


def _alert_late_clock_out(hours_offset=1):
    """Alert users to clock out at hour increments after shift end"""
    KEY = "alert-time-to-clock-out-%s-hour-late-%s"

    now = datetime.utcnow()

    role_to_user_models = _query_base()\
        .join(Timeclock,
            and_(
                Timeclock.role_id == Role.id,
                Timeclock.user_id == User.id,
            )
        )\
        .filter(
            # It's end of shift
            Shift2.stop <= (now - timedelta(hours=hours_offset)),
            Shift2.stop >= (now - timedelta(minutes=SEARCH_WINDOW_MINUTES) - timedelta(hours=hours_offset)),
            Timeclock.start != None,
            Timeclock.stop == None,
            # And the timeclock was started during the shift
            Timeclock.start < Shift2.stop,
        )\
        .all()

    for rtu in role_to_user_models:
        # Use role to user id instead of user - multiple roles!
        if CronTimeclockNotificationSmsCache.lock(
            (KEY % (hours_offset, rtu.id))):
            user = rtu.user

            if hours_offset == 1:
                # Singular hour
                message = "Hey %s - You are still clocked in after your shift that ended one hour ago. Clock out here: %s" % (
                    user.first_name, current_app.config.get("URL"))
            else:
                # plural hours
                message = "Hey %s - You are still clocked in after your shift that ended %s hours ago. Clock out here: %s" % (
                    user.first_name, hours_offset,
                    current_app.config.get("URL"))

            user.send_sms(message)
