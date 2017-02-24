import json
from operator import itemgetter

from flask import current_app
from flask_restful import Resource
from sqlalchemy.sql import or_

from app.constants import API_ENVELOPE
from app.models import Organization, Location, Role, Schedule2
from app.plans import plans
from app import db
from app.apiv2.decorators import permission_sudo


class ScheduleMonitoringApi(Resource):
    @permission_sudo
    def get(self):

        chomp_queue = []
        chomp_processing = []
        mobius_queue = []
        mobius_processing = []

        schedules_in_progress = db.session.query(Schedule2, Role, Location, Organization).join(Role) \
            .join(Location) \
            .join(Organization) \
            .filter(
                or_(
                    Schedule2.state == "chomp-queue",
                    Schedule2.state == "chomp-processing",
                    Schedule2.state == "mobius-queue",
                    Schedule2.state == "mobius-processing",
                )
            ) \
            .all()

        for schedule, role, location, organization in schedules_in_progress:

            # safely json load demand
            if schedule.demand:
                try:
                    demand = json.loads(schedule.demand)
                except Exception:
                    current_app.logger.warning(
                        "Unable to json parse demand for schedule id %d" %
                        schedule.id)
                    demand = None
            else:
                demand = None

            # datetime stuff might not be populated
            if schedule.last_update:
                last_update = schedule.last_update.isoformat()
            else:
                last_update = None

            if schedule.chomp_start:
                chomp_start = schedule.chomp_start.isoformat()
            else:
                chomp_start = None

            if schedule.mobius_start:
                mobius_start = schedule.mobius_start.isoformat()
            else:
                mobius_start = None

            state = str(schedule.state)

            temp_record = {
                "schedule_id": int(schedule.id),
                "role_id": int(role.id),
                "role": str(role.name),
                "location_id": int(location.id),
                "location": str(location.name),
                "organization_id": int(organization.id),
                "organization": str(organization.name),
                "paid": organization.paid(),
                "plan_id": organization.plan,
                "plan": plans.get(organization.plan).get("name"),
                "demand": demand,
                "chomp_start": chomp_start,
                "mobius_start": mobius_start,
                "last_update": last_update,
                "start": schedule.start.isoformat(),
                "state": state,
            }

            if state == "chomp-queue":
                chomp_queue.append(temp_record)
            elif state == "chomp-processing":
                chomp_processing.append(temp_record)
            elif state == "mobius-queue":
                mobius_queue.append(temp_record)
            elif state == "mobius-processing":
                mobius_processing.append(temp_record)

            # sort queued schedules by closest start time
            chomp_queue = sorted(chomp_queue, key=itemgetter("last_update"))
            mobius_queue = sorted(mobius_queue, key=itemgetter("last_update"))

            # sort processing schedules by earliest solver_start
            chomp_processing = sorted(
                chomp_processing, key=itemgetter("chomp_start"))
            mobius_processing = sorted(
                mobius_processing, key=itemgetter("mobius_start"))

        return {
            API_ENVELOPE: {
                "chomp": chomp_processing + chomp_queue,
                "mobius": mobius_processing + mobius_queue,
            }
        }
