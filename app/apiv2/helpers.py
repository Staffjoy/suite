from app.constants import DAYS_OF_WEEK, DAY_LENGTH
from app.models import User


def verify_days_of_week_struct(week, binary=False):
    """Given a dictionary, verify its keys are the correct days
    of the week and values are lists of 24 integers greater than zero.
    """

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


def user_filter(key, value):
    ''' Change username and email to lowercase '''
    LOWERCASE = ["username", "email"]
    if key in LOWERCASE:
        return value.lower()
    return value


def valid_email(email):
    if User.query.filter_by(email=email.lower().strip()).first():
        return False
    return True
