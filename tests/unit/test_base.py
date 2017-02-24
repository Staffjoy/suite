import unittest
import datetime
import pytz
from app import create_app, db
from app.models import Organization, Location, Role, RoleToUser, User, Schedule2


class BasicsTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('test')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        # Create an org
        self.organization = Organization(
            name="Test Organization",
            day_week_starts="monday",
            plan="per-seat-v1",
            active=True, )
        db.session.add(self.organization)
        db.session.commit()

        # Add a location
        self.location = Location(
            name="Test Location",
            organization_id=self.organization.id,
            timezone="America/Los_Angeles")
        db.session.add(self.location)
        db.session.commit()

        # create a role
        self.role = Role(name="Test Role", location_id=self.location.id)
        db.session.add(self.role)
        db.session.commit()

        # create a couple role workers
        self.user1 = User(name="Test User 1", email="testuser1@7bridg.es")
        db.session.add(self.user1)
        db.session.commit()

        self.user2 = User(name="Test User 2", email="testuser2@7bridg.es")
        db.session.add(self.user2)
        db.session.commit()

        # add the user to the role
        db.session.add(RoleToUser(user_id=self.user1.id, role_id=self.role.id))
        db.session.add(RoleToUser(user_id=self.user2.id, role_id=self.role.id))
        db.session.commit()

        # create organization admin
        self.admin = User(name="Admin 1", email="testadmin1@7bridg.es")

        db.session.add(self.admin)
        db.session.commit()

        self.organization.admins.append(self.admin)
        db.session.commit()

        # create location manager
        self.manager = User(
            name="Location Manager 1", email="testmanager1@7bridg.es")

        db.session.add(self.manager)
        db.session.commit()

        self.location.managers.append(self.manager)
        db.session.commit()

        # create a schedule
        local_tz = pytz.timezone("America/Los_Angeles")
        utc = pytz.timezone("UTC")
        start_local = local_tz.localize(datetime.datetime(2016, 2, 1))
        stop_local = start_local + datetime.timedelta(days=7)

        start_utc = start_local.astimezone(utc)
        stop_utc = stop_local.astimezone(utc)
        self.schedule = Schedule2.create(
            role_id=self.role.id, start=start_utc, stop=stop_utc)

    def tearDown(self):
        db.session.remove()
        # Refresh db
        db.drop_all()
        self.app_context.pop()
