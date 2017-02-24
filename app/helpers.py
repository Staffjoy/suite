from datetime import datetime
import math
import iso8601
import pytz
from flask import current_app, request
from app.constants import DAY_LENGTH, DAYS_OF_WEEK


def is_native():
    """Tell whether request comes from native"""

    if request.cookies.get(
            current_app.config.get("NATIVE_COOKIE_NAME")) == "1":
        return True
    return False


def date_duration(date_obj):
    """
    takes an Iso8601 timestamp string and returns a string of
    the amount of time that has passed (e.g. "3 minutes ago")
    """

    default_tz = get_default_tz()

    if type(date_obj) is not datetime:
        date_obj = iso8601.parse_date(date_obj)
        date_obj = (date_obj + date_obj.utcoffset()).replace(tzinfo=default_tz)
    else:
        date_obj = default_tz.localize(date_obj)

    now = default_tz.localize(datetime.utcnow())
    seconds = int((now - date_obj).total_seconds())

    if seconds < 6:
        return "Just now"

    days = math.floor(seconds / 86400)
    seconds = seconds - (days * 86400)
    hours = math.floor(seconds / 3600)
    seconds = seconds - (hours * 3600)
    minutes = math.floor(seconds / 60)
    seconds = seconds - (minutes * 60)

    result = ""

    # Don't show seconds if it's been over 10 min
    if minutes < 10 and hours == 0 and days == 0:
        result = ("%d sec" % seconds) + result

    if minutes > 0 and days == 0:
        result = ("%d min " % minutes) + result

    if hours > 0:
        result = ("%d hr " % hours) + result

    if days > 0:
        result = ("%d days " % days) + result

    return "%s ago" % result


def sorted_sessions(sessions):
    """takes sessions dictionary and returns a sorted list"""
    for key in sessions.keys():
        sessions[key]["key"] = key

    return sorted(
        sessions.values(),
        key=lambda session: session["last_used"],
        reverse=True)


def verify_days_of_week_struct(week, binary=False):
    """ Given a dictionary, verify its keys are the correct days of the week and values are lists of 24 integers greater than zero."""

    if set(DAYS_OF_WEEK) != set(week.keys()):
        return False

    # Each day must be a list of ints
    for _, v in week.iteritems():
        if not isinstance(v, list):
            return False

        if len(v) != DAY_LENGTH:
            return False

        # Every item should be an int >= 0
        for d in v:
            if not isinstance(d, int):
                return False
            if d < 0:
                return False
            if d > 1 and binary is True:
                return False

    return True


def normalize_to_midnight(dt_obj):
    """sets the datetime obj to midnight time"""
    return dt_obj.replace(hour=0, minute=0, second=0, microsecond=0)


def check_datetime_is_midnight(dt_obj):
    """returns True if a given datetime object is set for midnight"""
    return dt_obj.hour + dt_obj.minute + dt_obj.second + dt_obj.microsecond == 0


def timespans_overlap(a_start, a_stop, b_start, b_stop):
    """
    returns True if A intersects with B

    A and B are defiend as abstract start and ends and can be as follows
        - Integers
        - Datetimes
    """

    # Case 1: B is within A
    if a_start <= b_start and a_stop >= b_stop:
        return True

    # Case 2: B ends during A
    if a_start >= b_start and a_start < b_stop:
        return True

    # Case 3: B starts during A
    if a_stop > b_start and a_stop <= b_stop:
        return True

    return False


def get_default_tz():
    """returns a pytz instance of the default timezone"""

    return pytz.timezone(current_app.config.get("DEFAULT_TIMEZONE"))
