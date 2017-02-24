import pytest

from tests.smoke.organizations.locations.roles.base_role import BaseRole


class TestRoles(BaseRole):
    def setUp(self):
        # (if you are copying and pasting, update class title below)
        super(TestRoles, self).setUp()

    def tearDown(self):
        # (if you are copying and pasting, update class title below)
        super(TestRoles, self).tearDown()

    # Modify Role
    def test_role_crud_sudo(self):
        self.update_permission_sudo()
        new_min_hours_per_workday = 2
        self.role.patch(min_hours_per_workday=new_min_hours_per_workday)
        assert self.role.data.get(
            "min_hours_per_workday") == new_min_hours_per_workday

        # delete
        self.role.delete()
        refetch = self.location.get_role(self.role.get_id())
        assert refetch.data.get("archived") is True

    def test_role_crud_admin(self):
        self.update_permission_admin()

        # post
        new_name = "Fisherman"
        new_role = self.location.create_role(name=new_name)
        assert new_role.data.get("name") == new_name

        # in other location
        new_role = self.other_location.create_role(name=new_name)
        assert new_role.data.get("name") == new_name

        # patch - works within all locations
        new_min_hours_per_workday = 2
        self.role.patch(min_hours_per_workday=new_min_hours_per_workday)
        assert self.role.data.get(
            "min_hours_per_workday") == new_min_hours_per_workday

        self.other_role.patch(min_hours_per_workday=new_min_hours_per_workday)
        assert self.other_role.data.get(
            "min_hours_per_workday") == new_min_hours_per_workday

        # delete
        self.role.delete()
        refetch = self.location.get_role(self.role.get_id())
        assert refetch.data.get("archived") is True

        self.other_role.delete()
        refetch = self.other_location.get_role(self.other_role.get_id())
        assert refetch.data.get("archived") is True

    def test_role_crud_manager(self):
        self.update_permission_manager()

        # post - only in managed locations
        new_name = "Fisherman"
        new_role = self.location.create_role(name=new_name)
        assert new_role.data.get("name") == new_name

        # fails in other location
        with pytest.raises(Exception):
            self.other_location.create_role(name=new_name)

        # patch - only in managed locations
        new_min_hours_per_workday = 2
        self.role.patch(min_hours_per_workday=new_min_hours_per_workday)
        assert self.role.data.get(
            "min_hours_per_workday") == new_min_hours_per_workday

        with pytest.raises(Exception):
            self.other_role.patch(
                min_hours_per_workday=new_min_hours_per_workday)

        # delete
        self.role.delete()
        refetch = self.location.get_role(self.role.get_id())
        assert refetch.data.get("archived") is True

        with pytest.raises(Exception):
            self.other_role.delete()

    def test_role_crud_worker(self):
        self.update_permission_worker()

        # post
        with pytest.raises(Exception):
            self.location.create_role(name="Fisherman")

        # patch
        with pytest.raises(Exception):
            self.role.patch(min_hours_per_workday=2)

        # delete
        with pytest.raises(Exception):
            self.role.delete()

        with pytest.raises(Exception):
            self.other_role.delete()
