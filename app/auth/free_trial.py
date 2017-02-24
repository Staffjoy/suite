from datetime import datetime, timedelta
import json
import random

import pytz
from flask import current_app, render_template

from app import db
from app.helpers import normalize_to_midnight
from app.models import User, Organization, RoleToUser, Role, Location, \
    Schedule2, Shift2, Timeclock

# Emails that are free users
# If you care about your inbox, don't activate these accounts
# (hence using euler@ instead of lenny@)
BARISTAS = [
    "feynman@7bridg.es", "rosalind@7bridg.es", "euler@7bridg.es",
    "planck@7bridg.es", "tesla@7bridg.es"
]
CASHIERS = ["dantzig@7bridg.es", "curie@7bridg.es"]

# shifts is a list of lists of tuples
# each list is all the shifts designated for each person
# each tuple descripes a specific shift
# a tuple is organized like this:
# (day_name, start, length)
# NOTE that day_name needs to be converted to the interger based on day_week_start

USER_BARISTA_SHIFTS = [("monday", 10, 4), ("wednesday", 8, 4),
                       ("thursday", 8, 4), ("friday", 10, 4)]

UNASSIGNED_BARISTA_SHIFTS = [("tuesday", 8, 4)]

BARISTA_SHIFTS = [[("monday", 8, 4), ("tuesday", 12, 4), ("wednesday", 8, 7),
                   ("thursday", 8, 7), ("friday", 12, 4)],
                  [("monday", 8, 5), ("tuesday", 8, 6), ("wednesday", 10, 4),
                   ("thursday", 10, 4), ("friday", 8, 4)],
                  [("monday", 11, 4), ("tuesday", 9, 6), ("wednesday", 12, 6),
                   ("thursday", 12, 6), ("friday", 8, 4)],
                  [("monday", 12, 4), ("tuesday", 10, 4), ("wednesday", 13, 4),
                   ("thursday", 13, 4), ("friday", 11, 4)],
                  [("monday", 13, 5), ("tuesday", 14, 4), ("wednesday", 9, 4),
                   ("thursday", 9, 4), ("friday", 12, 6)]]

CASHIER_SHIFTS = [[("monday", 8, 7), ("tuesday", 8, 7), ("wednesday", 10, 8),
                   ("thursday", 10, 8), ("friday", 8, 6)],
                  [("monday", 11, 7), ("tuesday", 11, 7), ("wednesday", 8, 8),
                   ("thursday", 8, 8), ("friday", 11, 7)]]

DAYS_IN_WEEK = [
    "monday", "tuesday", "wednesday", "thursday", "friday", "saturday",
    "sunday"
]


def make_day_mapping_dict(day_week_start):
    """
    given a day_week_start, creates a dictionary mapping each day of the week
    to 1-indexed positions

    e.g. day_week_start = 'tuesday' -> result["wednesday"] = 2
    """

    day_week_start = day_week_start.lower()

    if day_week_start not in DAYS_IN_WEEK:
        raise Exception("invalid day supplied to day mapping:\t%s" %
                        day_week_start)

    result = {}
    week_length = 7
    start_index = DAYS_IN_WEEK.index(day_week_start)

    for i, day in enumerate(DAYS_IN_WEEK):
        result[day] = (i + week_length - start_index) % week_length

    return result


def provision(form):
    # Make the user account

    user = User(
        email=form.email.data.lower().strip(),
        password=form.password.data,
        name=form.name.data.strip(),
        active=False,
        confirmed=False, )

    try:
        db.session.add(user)
        db.session.commit()
    except:
        db.session.rollback()
        raise Exception("Dirty session")
    user.flush_associated_shift_caches()

    # Send activation email
    token = user.generate_confirmation_token(trial=True)
    user.send_email("[Action Required] Activate Your Free Trial",
                    render_template(
                        "email/confirm-trial.html", user=user, token=token),
                    True)

    # Create an org
    organization = Organization(
        name=form.company_name.data,
        day_week_starts=form.day_week_starts.data.lower(),
        enterprise_access=form.enterprise_access.data == "yes",
        plan=form.plan.data,
        trial_days=current_app.config.get("FREE_TRIAL_DAYS"),
        active=True, )
    db.session.add(organization)
    db.session.commit()

    organization.admins.append(user)
    db.session.commit()

    # get timezone
    timezone_name = form.timezone.data.strip()

    if timezone_name not in pytz.all_timezones:
        timezone_name = current_app.config.get("DEFAULT_TIMEZONE")

    timezone = pytz.timezone(timezone_name)
    default_tz = pytz.timezone(current_app.config.get("DEFAULT_TIMEZONE"))

    # Add a location
    l = Location(
        name="Demo - Cafe",
        organization_id=organization.id,
        timezone=timezone_name)
    db.session.add(l)
    db.session.commit()

    # Add two roles
    r_barista = Role(name="Baristas", location_id=l.id)
    r_cashier = Role(name="Cashiers", location_id=l.id)
    db.session.add(r_barista)
    db.session.add(r_cashier)
    db.session.commit()

    barista_user_ids = []
    for email in BARISTAS:
        barista = User.query.filter_by(email=email.lower()).first()
        if barista is None:
            barista = User.create_and_invite(
                email,
                name="Demo User",
                silent=True,  # Silence on dev
            )
        barista_user_ids.append(barista.id)
        db.session.add(RoleToUser(user_id=barista.id, role_id=r_barista.id))
        db.session.commit()

    # Add the current user as a barista too
    db.session.add(RoleToUser(user_id=user.id, role_id=r_barista.id))
    db.session.commit()

    cashier_user_ids = []
    for email in CASHIERS:
        cashier = User.query.filter_by(email=email.lower()).first()
        if cashier is None:
            cashier = User.create_and_invite(
                email,
                name="Demo User",
                silent=True,  # Silence on dev
            )

        cashier_user_ids.append(cashier.id)

        # cashiers are full time, so they inherit max_hours_per_week at 40 instead of 29
        db.session.add(
            RoleToUser(
                user_id=cashier.id,
                role_id=r_cashier.id,
                max_half_hours_per_workweek=80))
        db.session.commit()

    # Load schedule data
    barista_demand = json.loads(
        '{"monday":[0,0,0,0,0,0,0,0,2,2,3,4,4,4,3,2,1,1,0,0,0,0,0,0],"tuesday":[0,0,0,0,0,0,0,0,2,3,4,4,4,4,3,2,1,1,0,0,0,0,0,0],"wednesday":[0,0,0,0,0,0,0,0,2,3,4,4,4,4,3,2,2,1,0,0,0,0,0,0],"thursday":[0,0,0,0,0,0,0,0,2,3,4,4,4,4,3,2,2,1,0,0,0,0,0,0],"friday":[0,0,0,0,0,0,0,0,2,2,3,4,4,4,3,2,1,1,0,0,0,0,0,0],"saturday":[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],"sunday":[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]}'
    )
    cashier_demand = json.loads(
        '{"monday":[0,0,0,0,0,0,0,0,1,1,1,2,2,2,2,1,1,1,0,0,0,0,0,0],"tuesday":[0,0,0,0,0,0,0,0,1,1,1,2,2,2,2,1,1,1,0,0,0,0,0,0],"wednesday":[0,0,0,0,0,0,0,0,1,1,2,2,2,2,2,2,1,1,0,0,0,0,0,0],"thursday":[0,0,0,0,0,0,0,0,1,1,2,2,2,2,2,2,1,1,0,0,0,0,0,0],"friday":[0,0,0,0,0,0,0,0,1,1,1,2,2,2,1,1,1,1,0,0,0,0,0,0],"saturday":[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],"sunday":[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]}'
    )

    # Have 4 schedules
    done_schedule_start_local = timezone.localize(
        normalize_to_midnight(datetime.utcnow() + timedelta(days=1)))
    done_schedule_start = done_schedule_start_local.astimezone(default_tz)

    # Increment until we get the correct starting day of week
    # (be cautious here due to infinite loop possibility)
    ttl = 7  # Prevent infinite loops
    while (done_schedule_start_local.strftime("%A").lower() !=
           organization.day_week_starts.lower() and ttl > 0):

        done_schedule_start_local = normalize_to_midnight(
            (done_schedule_start + timedelta(days=1, hours=1)
             ).astimezone(timezone))
        done_schedule_start = done_schedule_start_local.astimezone(default_tz)
        ttl -= 1

    if ttl == 0:
        raise Exception("Unable to match day of week")

    done_schedule_start = done_schedule_start_local.astimezone(default_tz)
    done_schedule_stop = normalize_to_midnight(
        (done_schedule_start + timedelta(days=7, hours=1)
         ).astimezone(timezone)).astimezone(default_tz)
    current_schedule_start = normalize_to_midnight(
        (done_schedule_start - timedelta(days=6, hours=23)
         ).astimezone(timezone)).astimezone(default_tz)
    past_schedule_start = normalize_to_midnight(
        (done_schedule_start - timedelta(days=13, hours=23)
         ).astimezone(timezone)).astimezone(default_tz)

    # Make the schedules

    # the previous week
    barista_schedule_past = Schedule2.create(
        role_id=r_barista.id,
        start=past_schedule_start,
        stop=current_schedule_start,
        state="published",
        demand=barista_demand)
    cashier_schedule_past = Schedule2.create(
        role_id=r_cashier.id,
        start=past_schedule_start,
        stop=current_schedule_start,
        state="published",
        demand=cashier_demand)

    # the current week
    barista_schedule_current = Schedule2.create(
        role_id=r_barista.id,
        start=current_schedule_start,
        stop=done_schedule_start,
        state="published",
        demand=barista_demand)
    cashier_schedule_current = Schedule2.create(
        role_id=r_cashier.id,
        start=current_schedule_start,
        stop=done_schedule_start,
        state="published",
        demand=cashier_demand)

    # next week (schedule is published)
    barista_schedule_done = Schedule2.create(
        role_id=r_barista.id,
        start=done_schedule_start,
        stop=done_schedule_stop,
        state="published",
        demand=barista_demand)
    cashier_schedule_done = Schedule2.create(
        role_id=r_cashier.id,
        start=done_schedule_start,
        stop=done_schedule_stop,
        state="published",
        demand=cashier_demand)

    day_mapping = make_day_mapping_dict(organization.day_week_starts)

    # along with each shift, create a timeclock record if the date is before this cutoff
    timeclock_cutoff = normalize_to_midnight(datetime.utcnow())

    # add barista shifts
    for i, set_of_shifts in enumerate(BARISTA_SHIFTS):
        for schedule in [
                barista_schedule_past, barista_schedule_current,
                barista_schedule_done
        ]:

            for shift_tuple in set_of_shifts:
                current_date = schedule.start + timedelta(
                    days=day_mapping[shift_tuple[0]])
                shift_start = current_date + timedelta(hours=shift_tuple[1])
                shift_stop = shift_start + timedelta(hours=shift_tuple[2])

                s = Shift2(
                    role_id=schedule.role_id,
                    user_id=barista_user_ids[i],
                    start=shift_start,
                    stop=shift_stop,
                    published=True)

                db.session.add(s)
                db.session.commit()

                # create a timeclock if appropriate
                if current_date < timeclock_cutoff:

                    # this will make 7% of the timeclocks needed be empty
                    if random.randint(1, 14) == 14:
                        continue

                    start_minutes = random.randrange(-3, 8)
                    start_seconds = random.randrange(-30, 31)

                    stop_minutes = random.randrange(-3, 15)
                    stop_seconds = random.randrange(-30, 31)

                    start = shift_start + timedelta(
                        minutes=start_minutes, seconds=start_seconds)
                    stop = shift_stop + timedelta(
                        minutes=stop_minutes, seconds=stop_seconds)

                    t = Timeclock(
                        role_id=schedule.role_id,
                        user_id=barista_user_ids[i],
                        start=start,
                        stop=stop)

                    db.session.add(t)
                    db.session.commit()

    # add cashier shifts
    for i, set_of_shifts in enumerate(CASHIER_SHIFTS):
        for schedule in [
                cashier_schedule_past, cashier_schedule_current,
                cashier_schedule_done
        ]:

            for shift_tuple in set_of_shifts:
                current_date = schedule.start + timedelta(
                    days=day_mapping[shift_tuple[0]])
                shift_start = current_date + timedelta(hours=shift_tuple[1])
                shift_stop = shift_start + timedelta(hours=shift_tuple[2])

                s = Shift2(
                    role_id=schedule.role_id,
                    user_id=cashier_user_ids[i],
                    start=shift_start,
                    stop=shift_stop,
                    published=True)

                db.session.add(s)
                db.session.commit()

                # create a timeclock if appropriate
                if current_date < timeclock_cutoff:

                    # this will make 7% of the timeclocks needed be empty
                    if random.randint(1, 14) == 14:
                        continue

                    start_minutes = random.randrange(-3, 8)
                    start_seconds = random.randrange(-30, 31)

                    stop_minutes = random.randrange(-3, 15)
                    stop_seconds = random.randrange(-30, 31)

                    start = shift_start + timedelta(
                        minutes=start_minutes, seconds=start_seconds)
                    stop = shift_stop + timedelta(
                        minutes=stop_minutes, seconds=stop_seconds)

                    t = Timeclock(
                        role_id=schedule.role_id,
                        user_id=cashier_user_ids[i],
                        start=start,
                        stop=stop)

                    db.session.add(t)
                    db.session.commit()

    # add shifts for our dear user
    for schedule in [
            barista_schedule_past, barista_schedule_current,
            barista_schedule_done
    ]:

        for shift_tuple in USER_BARISTA_SHIFTS:

            current_date = schedule.start + timedelta(
                days=day_mapping[shift_tuple[0]])
            shift_start = current_date + timedelta(hours=shift_tuple[1])
            shift_stop = shift_start + timedelta(hours=shift_tuple[2])

            s = Shift2(
                role_id=schedule.role_id,
                user_id=user.id,
                start=shift_start,
                stop=shift_stop,
                published=True)

            db.session.add(s)
            db.session.commit()

            # create a timeclock if appropriate
            if current_date < timeclock_cutoff:

                start_minutes = random.randrange(-3, 8)
                start_seconds = random.randrange(-30, 31)

                stop_minutes = random.randrange(-3, 15)
                stop_seconds = random.randrange(-30, 31)

                start = shift_start + timedelta(
                    minutes=start_minutes, seconds=start_seconds)
                stop = shift_stop + timedelta(
                    minutes=stop_minutes, seconds=stop_seconds)

                t = Timeclock(
                    role_id=schedule.role_id,
                    user_id=user.id,
                    start=start,
                    stop=stop)

                db.session.add(t)
                db.session.commit()

    # add unassigned shifts to barista
    for shift_tuple in UNASSIGNED_BARISTA_SHIFTS:
        shift_start = barista_schedule_done.start + timedelta(
            days=day_mapping[shift_tuple[0]], hours=shift_tuple[1])
        shift_stop = shift_start + timedelta(hours=shift_tuple[2])
        s = Shift2(
            role_id=barista_schedule_done.role_id,
            start=shift_start,
            stop=shift_stop,
            published=True)

        db.session.add(s)
        db.session.commit()

    current_app.logger.info(
        "Created a free trial for user %s (id %s) - org %s (id %s)" %
        (user.email, user.id, organization.name, organization.id))
    return
