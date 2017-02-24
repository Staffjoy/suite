import pytest

from tests.smoke.organizations.base_organization import BaseOrganization


class TestOrganizations(BaseOrganization):
    def setUp(self):
        # (if you are copying and pasting, update class title below)
        super(TestOrganizations, self).setUp()

    def tearDown(self):
        # (if you are copying and pasting, update class title below)
        super(TestOrganizations, self).tearDown()

    # Org Crud
    def test_org_crud_sudo(self):
        self.update_permission_sudo()

        # an org was created in the setup

        # patch
        new_name = "Fred"
        self.organization.patch(name=new_name)
        assert self.organization.data.get("name") == new_name

        # orgs cannot be deleted
        with pytest.raises(Exception):
            self.organization.delete()

    def test_org_crud_admin(self):
        self.update_permission_admin()

        # post
        with pytest.raises(Exception):
            self.root_client.create_organization(name="Failure Test Org")

        # patch
        new_name = "Fred"
        self.organization.patch(name=new_name)
        assert self.organization.data.get("name") == new_name

        # orgs cannot be deleted
        with pytest.raises(Exception):
            self.organization.delete()

    def test_org_crud_manager(self):
        self.update_permission_manager()

        # post
        with pytest.raises(Exception):
            self.root_client.create_organization(name="Failure Test Org")

        # patch
        with pytest.raises(Exception):
            self.organization.patch(name="fred")

        # orgs cannot be deleted
        with pytest.raises(Exception):
            self.organization.delete()

    def test_org_crud_worker(self):
        self.update_permission_worker()

        # post
        with pytest.raises(Exception):
            self.root_client.create_organization(name="Failure Test Org")

        # patch
        with pytest.raises(Exception):
            self.organization.patch(name="fred")

        # orgs cannot be deleted
        with pytest.raises(Exception):
            self.organization.delete()
