import pytest

from tests.smoke.organizations.locations.managers.base_manager import BaseManager


class TestManagers(BaseManager):
    ADDITIONAL_MANAGER_EMAIL = "demo+manager2@7bridg.es"

    def setUp(self):
        # (if you are copying and pasting, update class title below)
        super(TestManagers, self).setUp()

    def tearDown(self):
        # (if you are copying and pasting, update class title below)
        super(TestManagers, self).tearDown()

    def test_manager_crud_sudo(self):
        # sudo creates an manager in the setup, so no need to test again

        self.manager.delete()
        with pytest.raises(Exception):
            self.location.get(self.manager.get_id())

    def test_manager_crud_admin(self):
        self.update_permission_admin()
        new_manager = self.location.create_manager(
            email=self.ADDITIONAL_MANAGER_EMAIL)
        assert new_manager.data.get("email") == self.ADDITIONAL_MANAGER_EMAIL

        # other locations work too
        new_manager = self.other_location.create_manager(
            email=self.ADDITIONAL_MANAGER_EMAIL)
        assert new_manager.data.get("email") == self.ADDITIONAL_MANAGER_EMAIL

        self.manager.delete()
        with pytest.raises(Exception):
            self.location.get(self.manager.get_id())

    def test_manager_crud_manager(self):
        self.update_permission_manager()
        new_manager = self.location.create_manager(
            email=self.ADDITIONAL_MANAGER_EMAIL)
        assert new_manager.data.get("email") == self.ADDITIONAL_MANAGER_EMAIL

        # will fail in other locations
        with pytest.raises(Exception):
            self.other_location.create_manager(
                email=self.ADDITIONAL_MANAGER_EMAIL)

        new_manager.delete()
        with pytest.raises(Exception):
            self.location.get(new_manager.get_id())

    def test_manager_crud_worker(self):
        self.update_permission_worker()
        with pytest.raises(Exception):
            self.location.create_manager(email=self.ADDITIONAL_MANAGER_EMAIL)

        # delete fails
        with pytest.raises(Exception):
            self.manager.delete()
