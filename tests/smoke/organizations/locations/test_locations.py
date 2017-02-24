import pytest

from tests.smoke.organizations.locations.base_location import BaseLocation


class TestLocations(BaseLocation):
    def setUp(self):
        # (if you are copying and pasting, update class title below)
        super(TestLocations, self).setUp()

    def tearDown(self):
        # (if you are copying and pasting, update class title below)
        super(TestLocations, self).tearDown()

    def test_location_crud_sudo(self):
        self.update_permission_sudo()

        # sudo creates a location in setup, don't need to do again

        # patch
        new_name = "Monterey"
        self.location.patch(name=new_name)
        assert self.location.data.get("name") == new_name

        # delete
        self.location.delete()

        # verify that it's archived
        refetch = self.organization.get_location(self.location.get_id())
        assert refetch.data.get("archived") is True

    def test_location_crud_admin(self):
        self.update_permission_admin()

        # post
        new_location_name = "Oakland"
        new_location = self.organization.create_location(
            name=new_location_name)
        assert new_location.data.get("name") == new_location_name

        # patch - works for both locations
        new_name = "Monterey"
        self.location.patch(name=new_name)
        assert self.location.data.get("name") == new_name

        self.update_permission_admin()
        new_name = "Monterey"
        self.other_location.patch(name=new_name)
        assert self.other_location.data.get("name") == new_name

        # delete
        self.location.delete()

        # verify that it's archived
        refetch = self.organization.get_location(self.location.get_id())
        assert refetch.data.get("archived") is True

    def test_location_crud_manager(self):
        self.update_permission_manager()

        # post - managers cannot create new locations
        with pytest.raises(Exception):
            self.organization.create_location(name="Oakland")

        # patch - only at managing sites
        new_name = "Monterey"
        self.location.patch(name=new_name)
        assert self.location.data.get("name") == new_name

        # other locations will fail
        with pytest.raises(Exception):
            self.other_location.patch(name="Monterey")

        # managers cannot delete a location
        with pytest.raises(Exception):
            self.location.delete()

    def test_location_crud_worker(self):
        self.update_permission_worker()

        # post
        with pytest.raises(Exception):
            self.organization.create_location(name="Oakland")

        # patch
        with pytest.raises(Exception):
            self.location.patch(name="Monterey")

        # delete
        with pytest.raises(Exception):
            self.location.delete()
