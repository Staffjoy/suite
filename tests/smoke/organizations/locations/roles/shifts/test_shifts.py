import pytest
from tests.smoke.organizations.locations.roles.shifts.base_shift import BaseShift


class TestShifts(BaseShift):
    def setUp(self):
        # (if you are copying and pasting, update class title below)
        super(TestShifts, self).setUp()

    def tearDown(self):
        # (if you are copying and pasting, update class title below)
        super(TestShifts, self).tearDown()

    def test_shifts_crud_sudo(self):
        self.update_permission_sudo()

        # sudo can view shifts
        shifts = self.role.get_shifts(
            start=self.range_start, end=self.range_stop)
        assert len(shifts) == 2

        # sudo can create a new shift in other roles
        other_role_shift = self.other_role.create_shift(
            start=self.assigned_shift.data.get("start"),
            stop=self.assigned_shift.data.get("stop"))
        assert other_role_shift.data.get(
            "start") == self.assigned_shift.data.get("start")
        assert other_role_shift.data.get(
            "stop") == self.assigned_shift.data.get("stop")

        # all the roles
        new_shift = self.role.create_shift(
            start=self.assigned_shift.data.get("start"),
            stop=self.assigned_shift.data.get("stop"))
        assert new_shift.data.get("start") == self.assigned_shift.data.get(
            "start")
        assert new_shift.data.get("stop") == self.assigned_shift.data.get(
            "stop")

        # sudo can assign shifts in future
        self.unassigned_shift.patch(user_id=self.worker.get_id())
        assert self.unassigned_shift.data.get(
            "user_id") == self.worker.get_id()

        # ... and the past
        self.assigned_shift.patch(user_id=self.worker.get_id())
        assert self.assigned_shift.data.get("user_id") == self.worker.get_id()

        # sudo can modify the start and stop of a shift
        new_shift.patch(
            start=self.unassigned_shift.data.get("start"),
            stop=self.unassigned_shift.data.get("stop"))
        assert new_shift.data.get("start") == self.unassigned_shift.data.get(
            "start")
        assert new_shift.data.get("stop") == self.unassigned_shift.data.get(
            "stop")

        # patch description
        new_description = "This is a good description"
        self.assigned_shift.patch(description=new_description)
        assert self.assigned_shift.data.get("description") == new_description

        # can't be too long
        with pytest.raises(Exception):
            self.assigned_shift.patch(description=(new_description * 100))

        # shifts can be deleted
        deleted = self.unassigned_shift.delete()
        assert deleted is None
        with pytest.raises(Exception):
            self.role.get_shift(self.unassigned_shift.get_id())

    def test_shifts_crud_admin(self):
        self.update_permission_admin()

        # admin can view shifts
        shifts = self.role.get_shifts(
            start=self.range_start, end=self.range_stop)
        assert len(shifts) == 2

        # admins can create a new shift in other roles
        other_role_shift = self.other_role.create_shift(
            start=self.assigned_shift.data.get("start"),
            stop=self.assigned_shift.data.get("stop"))
        assert other_role_shift.data.get(
            "start") == self.assigned_shift.data.get("start")
        assert other_role_shift.data.get(
            "stop") == self.assigned_shift.data.get("stop")

        # all the roles
        new_shift = self.role.create_shift(
            start=self.assigned_shift.data.get("start"),
            stop=self.assigned_shift.data.get("stop"))
        assert new_shift.data.get("start") == self.assigned_shift.data.get(
            "start")
        assert new_shift.data.get("stop") == self.assigned_shift.data.get(
            "stop")

        # admins can assign shifts in future
        self.unassigned_shift.patch(user_id=self.worker.get_id())
        assert self.unassigned_shift.data.get(
            "user_id") == self.worker.get_id()

        # ... and the past
        self.assigned_shift.patch(user_id=self.worker.get_id())
        assert self.assigned_shift.data.get("user_id") == self.worker.get_id()

        # admins can modify the start and stop of a shift
        new_shift.patch(
            start=self.unassigned_shift.data.get("start"),
            stop=self.unassigned_shift.data.get("stop"))
        assert new_shift.data.get("start") == self.unassigned_shift.data.get(
            "start")
        assert new_shift.data.get("stop") == self.unassigned_shift.data.get(
            "stop")

        # patch description
        new_description = "This is a good description"
        self.assigned_shift.patch(description=new_description)
        assert self.assigned_shift.data.get("description") == new_description

        # can't be too long
        with pytest.raises(Exception):
            self.assigned_shift.patch(description=(new_description * 100))

        # shifts can be deleted
        deleted = self.unassigned_shift.delete()
        assert deleted is None
        with pytest.raises(Exception):
            self.role.get_shift(self.unassigned_shift.get_id())

    def test_shifts_crud_manager(self):
        self.update_permission_manager()

        # worker can view shifts
        shifts = self.role.get_shifts(
            start=self.range_start, end=self.range_stop)
        assert len(shifts) == 2

        # managers cannot create a new shift in other roles
        with pytest.raises(Exception):
            self.other_role.create_shift(
                start=self.assigned_shift.data.get("start"),
                stop=self.assigned_shift.data.get("stop"))

        # but managers can create within their own role
        new_shift = self.role.create_shift(
            start=self.assigned_shift.data.get("start"),
            stop=self.assigned_shift.data.get("stop"))
        assert new_shift.data.get("start") == self.assigned_shift.data.get(
            "start")
        assert new_shift.data.get("stop") == self.assigned_shift.data.get(
            "stop")

        # managers can assign shifts in future
        self.unassigned_shift.patch(user_id=self.worker.get_id())
        assert self.unassigned_shift.data.get(
            "user_id") == self.worker.get_id()

        # ... and the past
        self.assigned_shift.patch(user_id=self.worker.get_id())
        assert self.assigned_shift.data.get("user_id") == self.worker.get_id()

        # managers can modify the start and stop of a shift
        new_shift.patch(
            start=self.unassigned_shift.data.get("start"),
            stop=self.unassigned_shift.data.get("stop"))
        assert new_shift.data.get("start") == self.unassigned_shift.data.get(
            "start")
        assert new_shift.data.get("stop") == self.unassigned_shift.data.get(
            "stop")

        # patch description
        new_description = "This is a good description"
        self.assigned_shift.patch(description=new_description)
        assert self.assigned_shift.data.get("description") == new_description

        # can't be too long
        with pytest.raises(Exception):
            self.assigned_shift.patch(description=(new_description * 100))

        # shifts can be deleted
        deleted = self.unassigned_shift.delete()
        assert deleted is None
        with pytest.raises(Exception):
            self.role.get_shift(self.unassigned_shift.get_id())

    def test_shifts_crud_worker(self):
        self.update_permission_worker()

        # worker cannot create a new shift
        with pytest.raises(Exception):
            self.role.create_shift(
                start=self.assigned_shift.data.get("start"),
                stop=self.assigned_shift.data.get("stop"))

        # worker can view shifts
        shifts = self.role.get_shifts(
            start=self.range_start, end=self.range_stop)
        assert len(shifts) == 2

        # worker can claim an unassigned shift
        self.unassigned_shift.patch(user_id=self.worker.get_id())
        assert self.unassigned_shift.data.get(
            "user_id") == self.worker.get_id()

        # worker cannot modify a start or stop of a shift
        with pytest.raises(Exception):
            self.unassigned_shift.patch(
                start=self.assigned_shift.data.get("start"),
                stop=self.assigned_shift.data.get("stop"))

        # worker cannot reassign a shift
        with pytest.raises(Exception):
            self.assigned_shift.patch(user_id=self.worker.get_id())

        # patch description banned too
        with pytest.raises(Exception):
            self.assigned_shift.patch(description="hello")

        # deleting is banned too
        with pytest.raises(Exception):
            self.unassigned_shift.delete()
