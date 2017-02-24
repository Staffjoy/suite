import pytest

from tests.smoke.organizations.admins.base_admin import BaseAdmin


class TestAdmins(BaseAdmin):
    ADDITIONAL_ADMIN_EMAIL = "demo+admin2@7bridg.es"

    def setUp(self):
        # (if you are copying and pasting, update class title below)
        super(TestAdmins, self).setUp()

    def tearDown(self):
        # (if you are copying and pasting, update class title below)
        super(TestAdmins, self).tearDown()

    def test_admin_crud_sudo(self):
        # sudo creates an admin in the setup, so no need to test again

        # delete
        self.admin.delete()
        with pytest.raises(Exception):
            self.organization.get_admin(self.admin.get_id())

    def test_admin_crud_admin(self):
        self.update_permission_admin()
        new_admin = self.organization.create_admin(
            email=self.ADDITIONAL_ADMIN_EMAIL)
        assert new_admin.data.get("email") == self.ADDITIONAL_ADMIN_EMAIL

        # delete
        new_admin.delete()
        with pytest.raises(Exception):
            self.organization.get_admin(new_admin.get_id())

    def test_admin_crud_manager(self):
        self.update_permission_manager()

        with pytest.raises(Exception):
            self.organization.create_admin(email=self.ADDITIONAL_ADMIN_EMAIL)

        with pytest.raises(Exception):
            self.admin.delete()

    def test_admin_crud_worker(self):
        self.update_permission_worker()

        with pytest.raises(Exception):
            self.organization.create_admin(email=self.ADDITIONAL_ADMIN_EMAIL)

        with pytest.raises(Exception):
            self.admin.delete()
