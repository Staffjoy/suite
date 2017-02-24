from flask import g
from flask_restful import abort, reqparse

from app.models import User, Organization, Location, RecurringShift, Role, \
    RoleToUser, Schedule2, Shift2, Timeclock, TimeOffRequest, ApiKey

# These functions all require a logged-in user


def permission_sudo(f):
    """ Only administrators can do this """

    def decorator(*args, **kwargs):
        if not g.current_user.is_sudo():
            abort(401)
        return f(*args, **kwargs)

    return decorator


def permission_self(f):
    """ Both suder and the user matching the id in the route can modify"""

    def decorator(*args, **kwargs):
        user_id = kwargs.get("user_id")
        if g.current_user.id != user_id and g.current_user.is_sudo(
        ) is not True:
            abort(401)
        return f(*args, **kwargs)

    return decorator


def verify_user_api_key(f):
    """Verify that the api key belongs to the user"""

    def decorator(*args, **kwargs):
        user_id = kwargs.get("user_id")
        key_id = kwargs.get("key_id")
        ApiKey.query\
            .filter_by(user_id=user_id, id=key_id)\
            .first_or_404()
        return f(*args, **kwargs)

    return decorator


def verify_org_location(f):
    """ Check whether the location id is in the org """

    def decorator(*args, **kwargs):
        org_id = kwargs.get("org_id")
        location_id = kwargs.get("location_id")

        location = Location.query.filter_by(
            organization_id=org_id, id=location_id).first()
        if location is None:
            abort(404)

        return f(*args, **kwargs)

    return decorator


def verify_org_admin(f):
    """ Check whether the user is an admin of the org """

    def decorator(*args, **kwargs):
        org_id = kwargs.get("org_id")
        user_id = kwargs.get("user_id")
        user = User.query.get_or_404(user_id)

        # 404 if not admin
        user.admin_of.filter_by(id=org_id).first_or_404()

        return f(*args, **kwargs)

    return decorator


def verify_org_location_role(f):
    """ Check whether the role is in the location is in the org """

    def decorator(*args, **kwargs):
        org_id = kwargs.get("org_id")
        location_id = kwargs.get("location_id")
        role_id = kwargs.get("role_id")

        role = Role.query.join(Location).join(Organization).filter(
            Role.id == role_id, Location.id == location_id,
            Organization.id == org_id).first()

        if role is None:
            abort(404)

        return f(*args, **kwargs)

    return decorator


def verify_org_location_role_schedule(f):
    """ Check whether the schedule is in role is in the location is in the org """

    def decorator(*args, **kwargs):
        org_id = kwargs.get("org_id")
        location_id = kwargs.get("location_id")
        role_id = kwargs.get("role_id")
        schedule_id = kwargs.get("schedule_id")

        schedule = Schedule2.query.join(Role).join(Location).join(
            Organization).filter(
                Schedule2.id == schedule_id, Role.id == role_id,
                Location.id == location_id, Organization.id == org_id).first()

        if schedule is None:
            abort(404)

        return f(*args, **kwargs)

    return decorator


def verify_org_location_role_shift(f):
    """ check whether this shift is part of the role, and so on """

    def decorator(*args, **kwargs):
        org_id = kwargs.get("org_id")
        location_id = kwargs.get("location_id")
        role_id = kwargs.get("role_id")
        shift_id = kwargs.get("shift_id")

        shift = Shift2.query.join(Role).join(Location).join(
            Organization).filter(Shift2.id == shift_id, Role.id == role_id,
                                 Location.id == location_id,
                                 Organization.id == org_id).first()

        if shift is None:
            abort(404)

        return f(*args, **kwargs)

    return decorator


def verify_org_location_role_recurring_shift(f):
    """ check whether this recurring shift is part of the role, and so on """

    def decorator(*args, **kwargs):
        org_id = kwargs.get("org_id")
        location_id = kwargs.get("location_id")
        role_id = kwargs.get("role_id")
        recurring_shift_id = kwargs.get("recurring_shift_id")

        RecurringShift.query \
            .join(Role) \
            .join(Location) \
            .join(Organization) \
            .filter(
                RecurringShift.id == recurring_shift_id,
                Role.id == role_id,
                Location.id == location_id,
                Organization.id == org_id
            ) \
            .first_or_404()

        return f(*args, **kwargs)

    return decorator


def verify_org_location_role_user(f):
    """ Check whether the user is in the location is in the org """

    def decorator(*args, **kwargs):
        org_id = kwargs.get("org_id")
        location_id = kwargs.get("location_id")
        role_id = kwargs.get("role_id")
        user_id = kwargs.get("user_id")

        user = RoleToUser.query.join(Role).join(Location).join(
            Organization).filter(
                RoleToUser.user_id == user_id, Role.id == role_id,
                Location.id == location_id, Organization.id == org_id).first()

        if user is None:
            abort(404)

        return f(*args, **kwargs)

    return decorator


def verify_org_location_role_user_timeclock(f):
    """
    Check whether the timeclock belongs to the user and
    that the user is in the ensuing role, location and org
    """

    def decorator(*args, **kwargs):
        org_id = kwargs.get("org_id")
        location_id = kwargs.get("location_id")
        role_id = kwargs.get("role_id")
        user_id = kwargs.get("user_id")
        timeclock_id = kwargs.get("timeclock_id")

        timeclock = Timeclock.query.join(User).join(Role).join(Location).join(
            Organization).filter(Timeclock.id == timeclock_id,
                                 User.id == user_id, Role.id == role_id,
                                 Location.id == location_id,
                                 Organization.id == org_id).first()

        if timeclock is None:
            abort(404)

        return f(*args, **kwargs)

    return decorator


def verify_org_location_role_user_time_off_request(f):
    """
    Check whether the time off request belongs to the user and
    that the user is in the ensuing role, location and org
    """

    def decorator(*args, **kwargs):
        org_id = kwargs.get("org_id")
        location_id = kwargs.get("location_id")
        role_id = kwargs.get("role_id")
        user_id = kwargs.get("user_id")
        time_off_request_id = kwargs.get("time_off_request_id")

        time_off_request = TimeOffRequest.query \
            .join(RoleToUser) \
            .join(Role) \
            .join(Location) \
            .join(Organization) \
            .filter(
                TimeOffRequest.id == time_off_request_id,
                RoleToUser.user_id == user_id,
                Role.id == role_id,
                Location.id == location_id,
                Organization.id == org_id
            ).first()

        if time_off_request is None:
            abort(404)

        return f(*args, **kwargs)

    return decorator


def permission_org_admin(f):
    """ Only administrators can do this """

    def decorator(*args, **kwargs):
        if g.current_user.is_sudo():
            return f(*args, **kwargs)

        if g.current_user.is_org_admin(org_id=kwargs.get("org_id")):
            return f(*args, **kwargs)

        abort(401)

    return decorator


def permission_org_member(f):
    """ org members, location managers, org admins, sudo  """

    def decorator(*args, **kwargs):
        if g.current_user.is_sudo():
            return f(*args, **kwargs)

        # org admins or all location managers
        if g.current_user.is_org_admin(org_id=kwargs.get(
                "org_id")) or g.current_user.is_manager_in_org(
                    org_id=kwargs.get("org_id")):
            return f(*args, **kwargs)

        # Check if user is a member of a role in the org
        memberships = g.current_user.memberships()
        for entry in memberships:
            if kwargs.get("org_id") == entry.get("organization_id"):
                return f(*args, **kwargs)

        abort(401)

    return decorator


def permission_location_manager(f):
    """ Only location managers can do this """

    def decorator(*args, **kwargs):
        if g.current_user.is_sudo():
            return f(*args, **kwargs)

        # org admins and location managers
        if g.current_user.is_org_admin_or_location_manager(
                org_id=kwargs.get("org_id"),
                location_id=kwargs.get("location_id")):
            return f(*args, **kwargs)

        abort(401)

    return decorator


def permission_location_member(f):
    """ Only admins and location members can do this """

    def decorator(*args, **kwargs):
        if g.current_user.is_sudo():
            return f(*args, **kwargs)

        # org admins, location admins, or members of the location
        if g.current_user.is_org_admin_or_location_manager(
                org_id=kwargs.get("org_id"), location_id=kwargs.get(
                    "location_id")) or g.current_user.is_location_worker(
                        location_id=kwargs.get("location_id")):
            return f(*args, **kwargs)

        abort(401)

    return decorator


def permission_location_manager_or_self(f):
    """ Only admins and self can do this """

    #NOTE - currently pulls user_id from request body, not route

    def decorator(*args, **kwargs):
        if g.current_user.is_sudo():
            return f(*args, **kwargs)

        Location.query.get_or_404(kwargs.get("location_id"))

        # organization admin or location manager
        if g.current_user.is_org_admin_or_location_manager(
                org_id=kwargs.get("org_id"),
                location_id=kwargs.get("location_id")):
            return f(*args, **kwargs)

        # Check if user_id in request body is self
        user_id = kwargs.get("user_id")

        # Check if user_id in request body is self
        if user_id is None:
            parser = reqparse.RequestParser()
            parser.add_argument("user_id", type=int)
            data = parser.parse_args()
            user_id = data.get("user_id")

        if user_id is None:
            abort(400)

        # check that user is in role and active
        RoleToUser.query \
            .filter_by(
                role_id=kwargs.get("role_id"),
                user_id=user_id,
                archived=False
            ) \
            .first_or_404()

        if user_id == g.current_user.id:
            return f(*args, **kwargs)

        abort(403)

    return decorator


def schedule_preference_modifiable(f):
    """ Check whether the associated schedule is in a state that can be modified """
    MODIFIABLE_SCHEDULE_STATES = [
        "initial", "unpublished", "chomp-queue", "chomp-processing"
    ]

    def decorator(*args, **kwargs):
        if g.current_user.is_sudo():
            return f(*args, **kwargs)

        schedule = Schedule2.query.get_or_404(kwargs.get("schedule_id"))
        state = schedule.state
        if state is None:
            abort(500)

        if state in MODIFIABLE_SCHEDULE_STATES:
            return f(*args, **kwargs)
        abort(400)

    return decorator
