from flask.ext.assets import Bundle

import os

# This file may look a little janky because, in some cases, order matters during
# import, and in other cases it doesn"t.


def default():
    base = "javascript"
    preload_individual = ["vendor/jquery-2.1.3.js"]
    folders = ["vendor/base"]
    individual = ["main.js"]

    return build_bundle(base, preload_individual, folders, individual)


def vendor_single_page():
    base = "javascript/vendor"
    # Backbone needs to come before basic auth
    preload_individual = [
        "spa-preloads/underscore.js", "spa-preloads/backbone.js",
        "spa-preloads/highcharts.js", "spa-preloads/highcharts-more.js",
        "spa-preloads/moment.js"
    ]
    folders = ["single-page-app"]
    individual = []
    return build_bundle(base, preload_individual, folders, individual)


def shared_single_page():
    """
    these files create the foundation for any staffjoy single page app
    """

    base = "javascript/shared"
    preload_individual = ["app.js", "util.js"]
    folders = ["app/views"]
    individual = [
        "app/views/base.js",
        "app/models/base.js",
        "app/models/admin.js",
        "app/models/location.js",
        "app/models/location_manager.js",
        "app/models/organization.js",
        "app/models/plan.js",
        "app/models/role.js",
        "app/models/root.js",
        "app/models/preference.js",
        "app/models/time_off_request.js",
        "app/models/timeclock.js",
        "app/models/recurring_shift.js",
        "app/models/schedule_timeclock.js",
        "app/models/schedule.js",
        "app/models/shift.js",
        "app/models/timezone.js",
        "app/models/user_role.js",
        "app/collections/base.js",
        "app/collections/admins.js",
        "app/collections/locations.js",
        "app/collections/location_attendance.js",
        "app/collections/location_managers.js",
        "app/collections/location_shifts.js",
        "app/collections/location_timeclocks.js",
        "app/collections/location_time_off_requests.js",
        "app/collections/plans.js",
        "app/collections/roles.js",
        "app/collections/timeclocks.js",
        "app/collections/recurring_shifts.js",
        "app/collections/schedules.js",
        "app/collections/schedule_shifts.js",
        "app/collections/schedule_time_off_requests.js",
        "app/collections/schedule_timeclocks.js",
        "app/collections/shifts.js",
        "app/collections/shift_eligible_workers.js",
        "app/collections/time_off_requests.js",
        "app/collections/timezones.js",
        "app/collections/user_roles.js",
        "main.js",
    ]

    return build_bundle(base, preload_individual, folders, individual)


def euler_app():
    base = "javascript"
    preload_individual = [
        "shared/app.js",
        "shared/util.js",
        "shared/app/views/base.js",
        "euler/app/models/base.js",
        "euler/app/models/kpis.js",
        "euler/app/models/organization.js",
        "euler/app/models/plan.js",
        "euler/app/models/schedule.js",
        "euler/app/models/user.js",
        "euler/app/collections/base.js",
        "euler/app/collections/organizations.js",
        "euler/app/collections/plans.js",
        "euler/app/collections/schedule_monitors.js",
        "euler/app/collections/users.js",
        "euler/app/routers/router.js",
    ]
    folders = ["euler/app/views"]
    individual = [
        "shared/main.js",
    ]

    return build_bundle(base, preload_individual, folders, individual)


def manager_app():
    base = "javascript/manager"
    preload_individual = []
    folders = ["app/views"]
    individual = [
        "app/routers/router.js",
    ]

    return build_bundle(base, preload_individual, folders, individual)


def myschedules_app():
    base = "javascript/myschedules"
    preload_individual = []
    folders = ["app/views"]
    individual = [
        "app/routers/router.js",
    ]

    return build_bundle(base, preload_individual, folders, individual)


def build_bundle(base, preload_individual, folders, individual):
    """ Build the list of .js file to load.
    Base defines the folder base. All files must be within this parent. No trailing slashes.
    Folders describes search paths within which all files (including nested folders) should be added.
    Individual describes individual files that should be loaded from the base. 

    Load order is:
      1) Preload individual files
      2) Folders, in order of the list
      3) Load individual files, in order of the list
    """
    f = []
    static_root = "%s/%s/" % (os.path.dirname(os.path.abspath(__file__)),
                              "static", )
    base_path = "%s%s" % (static_root, base)

    # Preloads
    for i in preload_individual:
        f.append("%s/%s" % (base, i))

    # Folders
    for folder in folders:
        for root, _, files in os.walk("%s/%s/" % (base_path, folder)):
            relative_path = root.replace(static_root, "")
            files.sort()
            for name in files:
                if name.endswith(".js"):
                    if relative_path[-1] == "/":
                        f.append("%s%s" % (relative_path, name))
                    else:
                        f.append("%s/%s" % (relative_path, name))

    for i in individual:
        f.append("%s/%s" % (base, i))

    return Bundle(*f, filters="rjsmin", output="compiled/%(version)s.js")
