import os
import datetime
import unittest
from staffjoy import Client, Resource

ADMIN_EMAIL = "demo+admin@7bridg.es"
MANAGER_EMAIL = "demo+manager@7bridg.es"
WORKER_EMAIL = "demo+worker@7bridg.es"
OTHER_WORKER_EMAIL = "demo+worker2@7bridg.es"


class BaseTest(unittest.TestCase):
    """Spin up a basic test"""

    ROOT_API_KEY = "staffjoydev"

    # Will also have instance variables of admin_api_key,
    # manager_api_key, and worker_api_key

    def setUp(self):
        """
        Prepares for a specific test - sets up an organization, location, role,
        and worker with an admin, manager. There is an API Key available for
        sudo, admin, manager, and worker

        It is expected that all tasks done in the setup are done by sudo
        Do NOT change the permissions in setup here, nor in children setups
        """

        self.root_client = Client(
            key=self.ROOT_API_KEY, env=os.environ.get("ENV", "dev"))

        # Create an org
        self.organization = self.root_client.create_organization(
            name="Test Org %s" % datetime.datetime.utcnow().isoformat(), )

        self.organization.patch(
            active=True, )

        # Create a location
        self.location = self.organization.create_location(
            name="San Francisco", )

        # Create a role
        self.role = self.location.create_role(
            name="Tester", )

        # Add an admin
        self.admin = self.organization.create_admin(
            email=ADMIN_EMAIL, )

        # Add a manager
        self.manager = self.location.create_manager(email=MANAGER_EMAIL)

        # Add a worker
        self.worker = self.role.create_worker(
            email=WORKER_EMAIL,
            min_hours_per_workweek=20,
            max_hours_per_workweek=40)

        # Create necessary API Keys
        admin_resource = self.root_client.get_user(id=self.admin.get_id())
        manager_resource = self.root_client.get_user(id=self.manager.get_id())
        worker_resource = self.root_client.get_user(id=self.worker.get_id())

        # The user needs these attributes to access the api!
        admin_resource.patch(active=True, confirmed=True)
        manager_resource.patch(active=True, confirmed=True)
        worker_resource.patch(active=True, confirmed=True)

        admin_api_key_resource = admin_resource.create_apikey(
            name="admin smoke test key")
        manager_api_key_resource = manager_resource.create_apikey(
            name="manager smoke test key")
        worker_api_key_resource = worker_resource.create_apikey(
            name="worker smoke test key")

        self.admin_api_key = admin_api_key_resource.data.get("key")
        self.manager_api_key = manager_api_key_resource.data.get("key")
        self.worker_api_key = worker_api_key_resource.data.get("key")

        # for testing managers who can only control certain locations
        self.other_location = self.organization.create_location(
            name="Sacramento")

        self.other_role = self.other_location.create_role(name="Drivers")

        self.other_worker = self.other_role.create_worker(
            email=OTHER_WORKER_EMAIL,
            min_hours_per_workweek=20,
            max_hours_per_workweek=40)
        other_worker_resource = self.root_client.get_user(
            id=self.other_worker.get_id())
        other_worker_resource.patch(active=True, confirmed=True)

        # finally, run cron so that schedules are created for the recently created entities
        self.root_client.cron()

    def tearDown(self):
        # TODO - delete stuff
        pass

    def update_permission_sudo(self):
        """updates all primary resources to use the sudo api key"""
        self._set_api_keys(self.ROOT_API_KEY)

    def update_permission_admin(self):
        """updates all primary resources to use the admin api key"""
        self._set_api_keys(self.admin_api_key)

    def update_permission_manager(self):
        """updates all primary resources to use the manager api key"""
        self._set_api_keys(self.manager_api_key)

    def update_permission_worker(self):
        """updates all primary resources to use the worker api key"""
        self._set_api_keys(self.worker_api_key)

    def _set_api_keys(self, key):
        """
        sets the root_client, organization, location, role, and worker resource to the
        specified API Key

        it is not intended that this function be called directly
        """

        for resource in vars(self):
            if isinstance(getattr(self, resource), Resource):
                getattr(self, resource).key = key
