import datetime
from flask import render_template, url_for
from app.helpers import get_default_tz
from app.models import User, RoleToUser, Organization, Location
from app.limiters import ShiftChangeNotificationLimiter, AvailableShiftsNotificationLimiter
from app.constants import SUDO_EXTERNAL_NAME, SUDO_EXTERNAL_EMAIL

NOTIFICATION_MINUTE_THRESHOLD = 20


def alert_email(user, subject, message, force_send=False):
    """ Send a basic alert email. Message should be in HTML. """
    # Use force_send when security is important
    user.send_email(
        "[Alert] %s" % subject,
        render_template("alert-email.html", user=user, message=message),
        force_send=force_send)


def alert_changed_shift(org_id, location_id, role_id, local_datetime, user_id):
    """Notify worker of changed shift"""
    # Start day is passed in instead of shift because shift could be deleted
    if user_id is None or user_id == 0:
        # Unassigned
        return

    user = User.query.get(user_id)
    if user is None:
        raise Exception("Bad user_id in notify_changed_shift")

    assoc = RoleToUser.query.filter_by(
        user_id=user_id, role_id=role_id, archived=False).first()
    if assoc is None:
        # The user is no longer in that role
        return

    org = Organization.query.get(org_id)
    if org is None:
        raise Exception("Bad org in notify_changed_shift")

    # Email if it's been 20 minutes since the last email
    # or they logged in since last one
    if not ShiftChangeNotificationLimiter.allowed_to_send(user):
        return

    planner_url = url_for(
        'myschedules.myschedules_app',
        org_id=org_id,
        location_id=location_id,
        role_id=role_id,
        user_id=user_id,
        _external=True)

    alert_email(
        user, "Changes to your %s shifts" % org.name,
        "Your manager has updated your upcoming shifts on %s. Please log into your Staffjoy account to view the latest schedule: \n <a href=\"%s\">%s</a>"
        % (local_datetime.strftime("%Y-%m-%d"), planner_url, planner_url))

    # Note that email was sent
    ShiftChangeNotificationLimiter.mark_sent(user)


def alert_available_shifts(org_id,
                           location_id,
                           role_id,
                           local_datetime,
                           users,
                           exclude_id=None):
    """
    send a message that shifts are available for claiming

    (optional) pass a user_id as exclude_id to skip sending an email
    """

    org = Organization.query.get(org_id)
    if org is None:
        raise Exception("Bad org in notify_changed_shift")

    for user in users:

        # this user will not get an email
        # e.g. You were removed from this shift, so we send an email out
        # but you shouldn't get that email
        if user.id == exclude_id:
            continue

        if not AvailableShiftsNotificationLimiter.allowed_to_send(user):
            return

        planner_url = url_for(
            'myschedules.myschedules_app',
            org_id=org_id,
            location_id=location_id,
            role_id=role_id,
            user_id=user.id,
            _external=True)

        alert_email(
            user, "New %s Shifts Available" % org.name,
            "New shifts are available on %s. To claim them, log into your Staffjoy account and visit My Schedules: \n <a href=\"%s\">%s</a>"
            % (local_datetime.strftime("%Y-%m-%d"), planner_url, planner_url))

        # Note that email was sent
        AvailableShiftsNotificationLimiter.mark_sent(user)


def alert_timeclock_change(timeclock, org_id, location_id, role_id,
                           original_start, original_stop, worker, manager):
    """
    - sends an email to manager and the worker from the timeclock
    - if timeclock is None, then it was deleted
    - original_start and timeclock.start must be a datetime
    - timeclock.stop or original_stop can be defined or None
        - their state will determine which email is sent
    """

    org = Organization.query.get(org_id)
    location = Location.query.get(location_id)

    default_tz = get_default_tz()
    local_tz = location.timezone_pytz

    original_start_local = default_tz.localize(original_start).astimezone(
        local_tz)

    original_start_date = original_start_local.strftime("%-m/%-d")

    if manager.is_sudo():
        manager_name = SUDO_EXTERNAL_NAME
        manager_email = SUDO_EXTERNAL_EMAIL
    else:
        manager_name = manager.name or manager.email
        manager_email = manager.email

    worker_name = worker.name or worker.email
    tc_email_format = "%-I:%M:%S %p %-m/%-d/%Y"

    week_start_date = org.get_week_start_from_datetime(
        original_start_local).strftime("%Y-%m-%d")

    manager_url = "%s#locations/%s/attendance/%s" % (url_for(
        'manager.manager_app', org_id=org_id, _external=True), location_id,
                                                     week_start_date)

    worker_url = "%s#week/%s" % (url_for(
        'myschedules.myschedules_app',
        org_id=org_id,
        location_id=location_id,
        role_id=role_id,
        user_id=worker.id,
        _external=True), week_start_date)

    manager_subject = "Confirmation of timeclock change for %s on %s" % (
        worker_name, original_start_date)

    # the timeclock was deleted
    if timeclock is None:

        # if timeclock was open while deleted, log it as if it were just closed
        if original_stop is None:
            original_stop_local = default_tz.localize(
                original_stop).astimezone(local_tz)
        else:
            original_stop_local = default_tz.localize(
                datetime.datetime.utcnow()).astimezone(local_tz)

        manager_message = render_template(
            "email/timeclock/manager/deleted.html",
            user=manager,
            worker_name=worker_name,
            original_start_date=original_start_date,
            before_start=original_start_local.strftime(tc_email_format),
            before_stop=original_stop_local.strftime(tc_email_format),
            url=manager_url)

        worker_subject = "[Alert] Your %s manager deleted a timeclock on %s" % (
            org.name, original_start_date)
        worker_message = render_template(
            "email/timeclock/worker/deleted.html",
            user=worker,
            org_name=org.name,
            manager_name=manager_name,
            manager_email=manager_email,
            original_start_date=original_start_date,
            before_start=original_start_local.strftime(tc_email_format),
            before_stop=original_stop_local.strftime(tc_email_format),
            url=worker_url)

    # timeclock was modified
    else:
        new_start_local = default_tz.localize(
            timeclock.start).astimezone(local_tz)

        if original_stop is None:

            # start time was adjusted
            if timeclock.stop is None:
                manager_message = render_template(
                    "email/timeclock/manager/adjust_start.html",
                    user=manager,
                    worker_name=worker_name,
                    before_start=original_start_local.strftime(
                        tc_email_format),
                    now_start=new_start_local.strftime(tc_email_format),
                    url=manager_url)

                worker_subject = "[Alert] Your %s manager adjusted the start of your timeclock on %s" % (
                    org.name, original_start_date)
                worker_message = render_template(
                    "email/timeclock/worker/adjust_start.html",
                    user=worker,
                    org_name=org.name,
                    manager_name=manager_name,
                    manager_email=manager_email,
                    original_start_date=original_start_date,
                    before_start=original_start_local.strftime(
                        tc_email_format),
                    now_start=new_start_local.strftime(tc_email_format),
                    url=worker_url)

            # manager clocked the worker out
            else:
                stop_local = default_tz.localize(
                    timeclock.stop).astimezone(local_tz)

                manager_message = render_template(
                    "email/timeclock/manager/clocked_out.html",
                    user=manager,
                    worker_name=worker_name,
                    before_start=original_start_local.strftime(
                        tc_email_format),
                    now_start=new_start_local.strftime(tc_email_format),
                    now_stop=stop_local.strftime(tc_email_format),
                    url=manager_url)

                worker_subject = "[Alert] Your %s manager has clocked you out" % org.name
                worker_message = render_template(
                    "email/timeclock/worker/clocked_out.html",
                    user=worker,
                    org_name=org.name,
                    manager_name=manager_name,
                    manager_email=manager_email,
                    before_start=original_start_local.strftime(
                        tc_email_format),
                    now_start=new_start_local.strftime(tc_email_format),
                    now_stop=stop_local.strftime(tc_email_format),
                    url=worker_url)

                if worker.phone_number:
                    worker.send_sms("Your manager has clocked you out.")

        # completed timeclock was modified
        else:
            original_stop_local = default_tz.localize(
                original_stop).astimezone(local_tz)
            new_stop_local = default_tz.localize(
                timeclock.stop).astimezone(local_tz)

            manager_message = render_template(
                "email/timeclock/manager/adjusted.html",
                user=manager,
                worker_name=worker_name,
                original_start_date=original_start_date,
                before_start=original_start_local.strftime(tc_email_format),
                before_stop=original_stop_local.strftime(tc_email_format),
                now_start=new_start_local.strftime(tc_email_format),
                now_stop=new_stop_local.strftime(tc_email_format),
                url=manager_url)

            worker_subject = "[Alert] Your %s manager adjusted your timeclock on %s" % (
                org.name, original_start_date)
            worker_message = render_template(
                "email/timeclock/worker/adjusted.html",
                user=worker,
                org_name=org.name,
                manager_name=manager_name,
                manager_email=manager_email,
                original_start_date=original_start_date,
                before_start=original_start_local.strftime(tc_email_format),
                before_stop=original_stop_local.strftime(tc_email_format),
                now_start=new_start_local.strftime(tc_email_format),
                now_stop=new_stop_local.strftime(tc_email_format),
                url=worker_url)

    worker.send_email(worker_subject, worker_message, force_send=True)
    manager.send_email(manager_subject, manager_message, force_send=True)
