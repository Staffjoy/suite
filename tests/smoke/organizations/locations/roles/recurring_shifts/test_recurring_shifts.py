import pytest
from tests.smoke.organizations.locations.roles.recurring_shifts.base_recurring_shift import BaseRecurringShift


class TestRecurringShifts(BaseRecurringShift):
    def setUp(self):
        # (if you are copying and pasting, update class title below)
        super(TestRecurringShifts, self).setUp()

    def tearDown(self):
        # (if you are copying and pasting, update class title below)
        super(TestRecurringShifts, self).tearDown()

    def test_recurring_shifts_crud_sudo(self):
        self.update_permission_sudo()

        # get
        recurring_shifts = self.role.get_recurring_shifts()
        assert len(recurring_shifts) == 1

        other_recurring_shifts = self.other_role.get_recurring_shifts()
        assert len(other_recurring_shifts) == 1

        # post
        another_recurring_shift = self.role.create_recurring_shift(
            start_day="tuesday",
            start_hour=8,
            start_minute=0,
            duration_minutes=300,
            user_id=self.worker.get_id())
        assert another_recurring_shift.get_id() > 0
        assert another_recurring_shift.data.get("start_day") == "tuesday"

        # patch
        self.recurring_shift.patch(start_day="wednesday")
        assert self.recurring_shift.data.get("start_day") == "wednesday"

        self.other_recurring_shift.patch(start_day="wednesday")
        assert self.other_recurring_shift.data.get("start_day") == "wednesday"

        # delete
        another_recurring_shift.delete()
        with pytest.raises(Exception):
            self.role.get_recurring_shift(another_recurring_shift.get_id())

    def test_recurring_shifts_crud_admin(self):
        self.update_permission_admin()

        # get
        recurring_shifts = self.role.get_recurring_shifts()
        assert len(recurring_shifts) == 1

        other_recurring_shifts = self.other_role.get_recurring_shifts()
        assert len(other_recurring_shifts) == 1

        # post
        another_recurring_shift = self.role.create_recurring_shift(
            start_day="tuesday",
            start_hour=8,
            start_minute=0,
            duration_minutes=300,
            user_id=self.worker.get_id())
        assert another_recurring_shift.get_id() > 0
        assert another_recurring_shift.data.get("start_day") == "tuesday"

        yet_another_recurring_shift = self.other_role.create_recurring_shift(
            start_day="tuesday",
            start_hour=8,
            start_minute=0,
            duration_minutes=300,
            user_id=self.other_worker.get_id())
        assert yet_another_recurring_shift.get_id() > 0
        assert yet_another_recurring_shift.data.get("start_day") == "tuesday"

        # patch
        self.recurring_shift.patch(start_day="wednesday")
        assert self.recurring_shift.data.get("start_day") == "wednesday"

        self.other_recurring_shift.patch(start_day="wednesday")
        assert self.other_recurring_shift.data.get("start_day") == "wednesday"

        # delete
        another_recurring_shift.delete()
        with pytest.raises(Exception):
            self.role.get_recurring_shift(another_recurring_shift.get_id())

        yet_another_recurring_shift.delete()
        with pytest.raises(Exception):
            self.role.get_recurring_shift(yet_another_recurring_shift.get_id())

    def test_recurring_shifts_crud_manager(self):
        self.update_permission_manager()

        # get
        recurring_shifts = self.role.get_recurring_shifts()
        assert len(recurring_shifts) == 1

        with pytest.raises(Exception):
            self.other_role.get_recurring_shifts()

        # post
        another_recurring_shift = self.role.create_recurring_shift(
            start_day="tuesday",
            start_hour=8,
            start_minute=0,
            duration_minutes=300,
            user_id=self.worker.get_id())
        assert another_recurring_shift.get_id() > 0
        assert another_recurring_shift.data.get("start_day") == "tuesday"

        with pytest.raises(Exception):
            self.other_role.create_recurring_shift(
                start_day="tuesday",
                start_hour=8,
                start_minute=0,
                duration_minutes=300,
                user_id=self.other_worker.get_id())

        # patch
        self.recurring_shift.patch(start_day="wednesday")
        assert self.recurring_shift.data.get("start_day") == "wednesday"

        with pytest.raises(Exception):
            self.other_recurring_shift.patch(start_day="wednesday")

        # delete
        another_recurring_shift.delete()
        with pytest.raises(Exception):
            self.role.get_recurring_shift(another_recurring_shift.get_id())

        with pytest.raises(Exception):
            self.other_recurring_shift.delete()

    def test_recurring_shifts_crud_worker(self):
        self.update_permission_worker()

        # get
        recurring_shifts = self.role.get_recurring_shifts()
        assert len(recurring_shifts) == 1

        with pytest.raises(Exception):
            self.other_role.get_recurring_shifts()

        # post
        with pytest.raises(Exception):
            self.role.create_recurring_shift(
                start_day="tuesday",
                start_hour=8,
                start_minute=0,
                duration_minutes=300,
                user_id=self.worker.get_id())

        # patch
        with pytest.raises(Exception):
            self.recurring_shift.patch(start_day="wednesday")

        # delete
        with pytest.raises(Exception):
            self.recurring_shift.delete()
