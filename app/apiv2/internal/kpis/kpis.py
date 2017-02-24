from datetime import datetime, timedelta

from flask import current_app
from flask_restful import Resource

from sqlalchemy import func, distinct, select, not_
import iso8601

from app.apiv2.decorators import permission_sudo
from app.caches import PeopleScheduledPerWeekCache
from app.constants import API_ENVELOPE
from app.models import Shift2, User, Timeclock
from app import db

KPI_START = "2015-09-14T00:00:00Z"  # Monday UTC
ISO_DAY_FORMAT = "%Y-%m-%d"
WEEK_DAYS = 7
UNASSIGNED_USER_ID = 0


class KpisApi(Resource):
    method_decorators = [permission_sudo]

    def get(self):
        """Get KPI data"""

        return {
            API_ENVELOPE: {
                "people_scheduled_per_week": self._people_scheduled_per_week(),
                "people_clocked_in": self._people_clocked_in(),
                "people_on_shifts": self._people_on_shifts(),
                "people_online_in_last_day": self._people_online_in_last_day()
            }
        }

    def _people_scheduled_per_week(self):
        """Return distinct users scheduled per week"""
        week_start = iso8601.parse_date(KPI_START).replace(tzinfo=None)
        now = datetime.utcnow()
        people_scheduled_per_week = {}

        # Show current week and the following week
        while week_start <= (now):
            day = week_start.strftime(ISO_DAY_FORMAT)

            # Disable cache on dev. You'll thank me later.
            if current_app.config.get("DEBUG"):
                people = None
            else:
                people = PeopleScheduledPerWeekCache.get(day)

            if people is None:
                # Cache miss - find an set

                query = User.query.join(Shift2).filter(
                    Shift2.start >= week_start,
                    Shift2.start < (week_start + timedelta(days=7)))

                query = select([func.count(distinct(User.id))]).where(
                    Shift2.user_id == User.id)\
                    .where(Shift2.start >= week_start)\
                    .where(Shift2.start < (week_start + timedelta(days=7)))\
                    .select_from(Shift2).select_from(User)

                # Filter out staffjoy domains
                query = self._filter_not_staffjoy(query)

                people = db.session.execute(query).fetchone()[0]

                if (week_start + timedelta(days=WEEK_DAYS)) < now:
                    # Only cache if whole week has passed
                    PeopleScheduledPerWeekCache.set(day, people)

            people_scheduled_per_week[day] = people

            # Start next week
            week_start += timedelta(days=WEEK_DAYS)

        return people_scheduled_per_week

    def _people_on_shifts(self):
        """Return number of users with a shift active right now"""
        now = datetime.utcnow()
        query = select([func.count(distinct(User.id))])\
            .where(
            Shift2.user_id == User.id)\
            .where(Shift2.start <= now)\
            .where(Shift2.stop > now)\
            .select_from(Shift2).select_from(User)

        query = self._filter_not_staffjoy(query)

        return db.session.execute(query).fetchone()[0]

    def _people_clocked_in(self):
        """Return number of active timeclocks"""
        query = select([func.count(distinct(User.id))]).where(
            Timeclock.user_id == User.id)\
            .where(Timeclock.start != None)\
            .where(Timeclock.stop == None)\
            .select_from(Timeclock).select_from(User)

        query = self._filter_not_staffjoy(query)

        return db.session.execute(query).fetchone()[0]

    def _people_online_in_last_day(self):
        """Return number of users, not staffjoy, with activity in last day"""
        now = datetime.utcnow()
        query = select([func.count(distinct(User.id))])\
            .where(User.last_seen > (now - timedelta(days=1)))\
            .select_from(User)

        query = self._filter_not_staffjoy(query)

        return db.session.execute(query).fetchone()[0]

    @staticmethod
    def _filter_not_staffjoy(query):
        """Remove known Staffjoy emails"""
        for email in current_app.config.get("KPI_EMAILS_TO_EXCLUDE"):
            query = query.where(not_(User.email.like(email)))
        return query
