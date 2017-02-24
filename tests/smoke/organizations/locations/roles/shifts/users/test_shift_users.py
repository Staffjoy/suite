import pytest
from tests.smoke.organizations.locations.roles.shifts.users.base_shift_user import BaseShiftUser


class TestShiftUsers(BaseShiftUser):
    def setUp(self):
        # (if you are copying and pasting, update class title below)
        super(TestShiftUsers, self).setUp()

    def tearDown(self):
        # (if you are copying and pasting, update class title below)
        super(TestShiftUsers, self).tearDown()

    def test_shifts_users_crud_sudo(self):
        self.update_permission_sudo()
        eligible_workers = self.unassigned_shift.get_eligible_workers()
        assert len(eligible_workers) == 4

    def test_shift_users_crud_admin(self):
        self.update_permission_admin()
        eligible_workers = self.unassigned_shift.get_eligible_workers()
        assert len(eligible_workers) == 4

    def test_shift_users_crud_manager(self):
        self.update_permission_manager()
        eligible_workers = self.unassigned_shift.get_eligible_workers()
        assert len(eligible_workers) == 4

    def test_shifts_crud_worker(self):
        self.update_permission_worker()

        # workers cannot fetch this data
        with pytest.raises(Exception):
            self.unassigned_shift.get_eligible_workers()
