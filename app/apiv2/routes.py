from flask import g, request
from flask_restful import abort, marshal, Resource
from flask.ext.login import current_user

from app.apiv2.marshal import user_fields
from app.models import User, ApiKey

from app.apiv2 import apiv2_rest, apiv2

#
# Public
#

# organizations
from .organizations.organizations import OrganizationsApi
from .organizations.organization import OrganizationApi

# organization admins
from .organizations.admins.admins import OrgAdminsApi
from .organizations.admins.admin import OrgAdminApi

# organization workers
from .organizations.workers.organization_workers import OrganizationWorkersApi

# locations
from .organizations.locations.locations import LocationsApi
from .organizations.locations.location import LocationApi

# attendance
from .organizations.locations.attendance.location_attendance import LocationAttendanceApi

# location managers
from .organizations.locations.managers.managers import LocationManagersApi
from .organizations.locations.managers.manager import LocationManagerApi

# location shifts
from .organizations.locations.shifts.shifts import LocationShiftsApi

# location timeclocks
from .organizations.locations.timeclocks.timeclocks import LocationTimeclocksApi

# location timeoffrequests
from .organizations.locations.timeoffrequests.timeoffrequests import LocationTimeOffRequestsApi

# roles
from .organizations.locations.roles.roles import RolesApi
from .organizations.locations.roles.role import RoleApi

# schedules
from .organizations.locations.roles.schedules.schedules import SchedulesApi
from .organizations.locations.roles.schedules.schedule import ScheduleApi

# preferences
from .organizations.locations.roles.schedules.preferences.preferences import PreferencesApi
from .organizations.locations.roles.schedules.preferences.preference import PreferenceApi

# schedule shifts
from .organizations.locations.roles.schedules.shifts.shifts import ScheduleShiftsApi

# schedule timeclocks
from .organizations.locations.roles.schedules.timeclocks.timeclocks import ScheduleTimeclocksApi

# schedule time off requests
from .organizations.locations.roles.schedules.timeoffrequests.timeoffrequests import ScheduleTimeOffRequestsApi

# shifts
from .organizations.locations.roles.shifts.shifts import ShiftsApi
from .organizations.locations.roles.shifts.shift import ShiftApi

# eligible shift users
from .organizations.locations.roles.shifts.users.users import ShiftEligibleUsersApi

# shift query
from .organizations.locations.roles.shiftquery.shiftquery import ShiftQueryApi

# recurring shifts
from .organizations.locations.roles.recurring_shifts.recurring_shifts import RecurringShiftsApi
from .organizations.locations.roles.recurring_shifts.recurring_shift import RecurringShiftApi

# role members
from .organizations.locations.roles.users.users import RoleMembersApi
from .organizations.locations.roles.users.user import RoleMemberApi

# timeclocks
from .organizations.locations.roles.users.timeclocks.timeclocks import TimeclocksApi
from .organizations.locations.roles.users.timeclocks.timeclock import TimeclockApi

# time off requests
from .organizations.locations.roles.users.timeoffrequests.timeoffrequests import TimeOffRequestsApi
from .organizations.locations.roles.users.timeoffrequests.timeoffrequest import TimeOffRequestApi

# plans
from .plans.plans import PlansApi
from .plans.plan import PlanApi

# timezones
from .timezones.timezones import TimezonesApi

#
# Internal
#

# cron
from .internal.cron.cron import ShiftMechanic

# schedule monitoring
from .internal.schedule_monitoring.schedule_monitoring import ScheduleMonitoringApi

# tasking
from .internal.tasking.chomp_tasks import ChompTasksApi
from .internal.tasking.chomp_task import ChompTaskApi
from .internal.tasking.mobius_tasks import MobiusTasksApi
from .internal.tasking.mobius_task import MobiusTaskApi

# users
from .users.users import UsersApi
from .users.user import UserApi

# api keys
from .users.apikeys.apikeys import ApiKeysApi
from .users.apikeys.apikey import ApiKeyApi

# sessions
from .users.sessions.sessions import SessionsApi
from .users.sessions.session import SessionApi

# caches
from .internal.caches.caches import CachesApi
from .internal.caches.cache import CacheApi

# kpis
from .internal.kpis.kpis import KpisApi


@apiv2.before_request
def authenticate():
    ''' HTTP basic auth - just pass in token as user '''
    # Start assuming it's current user (session)
    g.current_user = current_user

    if request.authorization is not None:
        token = request.authorization.get("username")
        if token is None:
            abort(401)

        # Try a token - time-based auth used by our JS apps:
        token_user = User.verify_api_token(token)
        if token_user is not None:
            g.current_user = token_user
        else:
            # Try authenticating from perisistent api key:
            api_key_user = ApiKey.get_user(token)
            if api_key_user is not None:
                g.current_user = api_key_user

    try:
        if not g.current_user:
            abort(401)
    except:
        # in case globals not established
        abort(401)

    if not g.current_user.is_authenticated:
        abort(401)

    if not g.current_user.confirmed:
        abort(401)

    if not g.current_user.active:
        abort(401)

    g.current_user.ping()


class Root(Resource):
    """ Base of APIv2 """

    def get(self):
        result = {
            "data": marshal(g.current_user, user_fields),
            "resources": ["users", "organizations"],
            "access": {
                "organization_admin": [],
                "location_manager": [],
                "sudo": g.current_user.is_sudo(),
                "worker": g.current_user.membership_ids(),
            }
        }

        # add organization admins
        for org in g.current_user.admin_of.all():
            result["access"]["organization_admin"].append({
                "organization_id":
                org.id
            })

        # add location managers
        for location in g.current_user.manager_of.all():
            result["access"]["location_manager"].append({
                "organization_id":
                location.organization_id,
                "location_id":
                location.id
            })

        return result


apiv2_rest.add_resource(Root, "/")

# Public

# organizations
apiv2_rest.add_resource(OrganizationsApi, "/organizations/")
apiv2_rest.add_resource(OrganizationApi, "/organizations/<int:org_id>")

# organization admins
apiv2_rest.add_resource(OrgAdminsApi, "/organizations/<int:org_id>/admins/")
apiv2_rest.add_resource(OrgAdminApi,
                        "/organizations/<int:org_id>/admins/<int:user_id>")
# organization workers
apiv2_rest.add_resource(OrganizationWorkersApi,
                        "/organizations/<int:org_id>/workers/")

# locations
apiv2_rest.add_resource(LocationsApi, "/organizations/<int:org_id>/locations/")
apiv2_rest.add_resource(
    LocationApi, "/organizations/<int:org_id>/locations/<int:location_id>")

# attendance
apiv2_rest.add_resource(
    LocationAttendanceApi,
    "/organizations/<int:org_id>/locations/<int:location_id>/attendance/")

# location managers
apiv2_rest.add_resource(
    LocationManagersApi,
    "/organizations/<int:org_id>/locations/<int:location_id>/managers/")
apiv2_rest.add_resource(
    LocationManagerApi,
    "/organizations/<int:org_id>/locations/<int:location_id>/managers/<int:user_id>"
)

# location shifts
apiv2_rest.add_resource(
    LocationShiftsApi,
    "/organizations/<int:org_id>/locations/<int:location_id>/shifts/")

# location timeclocks
apiv2_rest.add_resource(
    LocationTimeclocksApi,
    "/organizations/<int:org_id>/locations/<int:location_id>/timeclocks/")

# location timeoffrequests
apiv2_rest.add_resource(
    LocationTimeOffRequestsApi,
    "/organizations/<int:org_id>/locations/<int:location_id>/timeoffrequests/")

# roles
apiv2_rest.add_resource(
    RolesApi, "/organizations/<int:org_id>/locations/<int:location_id>/roles/")
apiv2_rest.add_resource(
    RoleApi,
    "/organizations/<int:org_id>/locations/<int:location_id>/roles/<int:role_id>"
)

# schedules
apiv2_rest.add_resource(
    SchedulesApi,
    "/organizations/<int:org_id>/locations/<int:location_id>/roles/<int:role_id>/schedules/"
)
apiv2_rest.add_resource(
    ScheduleApi,
    "/organizations/<int:org_id>/locations/<int:location_id>/roles/<int:role_id>/schedules/<int:schedule_id>"
)

# preferences
apiv2_rest.add_resource(
    PreferencesApi,
    "/organizations/<int:org_id>/locations/<int:location_id>/roles/<int:role_id>/schedules/<int:schedule_id>/preferences/"
)
apiv2_rest.add_resource(
    PreferenceApi,
    "/organizations/<int:org_id>/locations/<int:location_id>/roles/<int:role_id>/schedules/<int:schedule_id>/preferences/<int:user_id>"
)

# schedule shifts
apiv2_rest.add_resource(
    ScheduleShiftsApi,
    "/organizations/<int:org_id>/locations/<int:location_id>/roles/<int:role_id>/schedules/<int:schedule_id>/shifts/"
)

# schedule timeclocks
apiv2_rest.add_resource(
    ScheduleTimeclocksApi,
    "/organizations/<int:org_id>/locations/<int:location_id>/roles/<int:role_id>/schedules/<int:schedule_id>/timeclocks/"
)

# schedule time off requests
apiv2_rest.add_resource(
    ScheduleTimeOffRequestsApi,
    "/organizations/<int:org_id>/locations/<int:location_id>/roles/<int:role_id>/schedules/<int:schedule_id>/timeoffrequests/"
)

# shifts
apiv2_rest.add_resource(
    ShiftsApi,
    "/organizations/<int:org_id>/locations/<int:location_id>/roles/<int:role_id>/shifts/"
)
apiv2_rest.add_resource(
    ShiftApi,
    "/organizations/<int:org_id>/locations/<int:location_id>/roles/<int:role_id>/shifts/<int:shift_id>"
)

# eligible shift users
apiv2_rest.add_resource(
    ShiftEligibleUsersApi,
    "/organizations/<int:org_id>/locations/<int:location_id>/roles/<int:role_id>/shifts/<int:shift_id>/users/"
)

# shift query
apiv2_rest.add_resource(
    ShiftQueryApi,
    "/organizations/<int:org_id>/locations/<int:location_id>/roles/<int:role_id>/shiftquery/"
)

# recurring shifts
apiv2_rest.add_resource(
    RecurringShiftsApi,
    "/organizations/<int:org_id>/locations/<int:location_id>/roles/<int:role_id>/recurringshifts/"
)
apiv2_rest.add_resource(
    RecurringShiftApi,
    "/organizations/<int:org_id>/locations/<int:location_id>/roles/<int:role_id>/recurringshifts/<int:recurring_shift_id>"
)

# role members
apiv2_rest.add_resource(
    RoleMembersApi,
    "/organizations/<int:org_id>/locations/<int:location_id>/roles/<int:role_id>/users/"
)
apiv2_rest.add_resource(
    RoleMemberApi,
    "/organizations/<int:org_id>/locations/<int:location_id>/roles/<int:role_id>/users/<int:user_id>"
)

# timeclocks
apiv2_rest.add_resource(
    TimeclocksApi,
    "/organizations/<int:org_id>/locations/<int:location_id>/roles/<int:role_id>/users/<int:user_id>/timeclocks/"
)
apiv2_rest.add_resource(
    TimeclockApi,
    "/organizations/<int:org_id>/locations/<int:location_id>/roles/<int:role_id>/users/<int:user_id>/timeclocks/<int:timeclock_id>"
)

# time off requests
apiv2_rest.add_resource(
    TimeOffRequestsApi,
    "/organizations/<int:org_id>/locations/<int:location_id>/roles/<int:role_id>/users/<int:user_id>/timeoffrequests/"
)
apiv2_rest.add_resource(
    TimeOffRequestApi,
    "/organizations/<int:org_id>/locations/<int:location_id>/roles/<int:role_id>/users/<int:user_id>/timeoffrequests/<int:time_off_request_id>"
)

# plans
apiv2_rest.add_resource(PlansApi, "/plans/")
apiv2_rest.add_resource(PlanApi, "/plans/<plan_id>")

# timezones
apiv2_rest.add_resource(TimezonesApi, "/timezones/")

# users
apiv2_rest.add_resource(UsersApi, "/users/")
apiv2_rest.add_resource(UserApi, "/users/<int:user_id>")

# api keys
apiv2_rest.add_resource(ApiKeysApi, "/users/<int:user_id>/apikeys/")
apiv2_rest.add_resource(ApiKeyApi, "/users/<int:user_id>/apikeys/<key_id>")

# sessions
apiv2_rest.add_resource(SessionsApi, "/users/<int:user_id>/sessions/")
apiv2_rest.add_resource(SessionApi,
                        "/users/<int:user_id>/sessions/<session_id>")

# Internal

# cron
apiv2_rest.add_resource(ShiftMechanic, "/internal/cron/")

# schedule monitoring
apiv2_rest.add_resource(ScheduleMonitoringApi, "/internal/schedulemonitoring/")

# tasking
apiv2_rest.add_resource(ChompTasksApi, "/internal/tasking/chomp/")
apiv2_rest.add_resource(ChompTaskApi,
                        "/internal/tasking/chomp/<int:schedule_id>")
apiv2_rest.add_resource(MobiusTasksApi, "/internal/tasking/mobius/")
apiv2_rest.add_resource(MobiusTaskApi,
                        "/internal/tasking/mobius/<int:schedule_id>")

apiv2_rest.add_resource(CachesApi, "/internal/caches/")
apiv2_rest.add_resource(CacheApi, "/internal/caches/<cache_key>")

apiv2_rest.add_resource(KpisApi, "/internal/kpis/")
