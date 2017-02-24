from tests.smoke.organizations.locations.roles.schedules.shifts.base_schedule_shift import BaseScheduleShift


class TestScheduleShifts(BaseScheduleShift):
    def setUp(self):
        # (if you are copying and pasting, update class title below)
        super(TestScheduleShifts, self).setUp()

    def tearDown(self):
        # (if you are copying and pasting, update class title below)
        super(TestScheduleShifts, self).tearDown()

    def test_schedule_shifts_crud_sudo(self):
        self.update_permission_sudo()

        all_shifts = self.schedule.get_schedule_shifts()
        claimable_shifts = self.schedule.get_schedule_shifts(
            claimable_by_user=self.worker.get_id())

        assert len(all_shifts) == 3
        assert len(claimable_shifts) == 2

    def test_schedule_shifts_crud_admin(self):
        self.update_permission_admin()

        all_shifts = self.schedule.get_schedule_shifts()
        claimable_shifts = self.schedule.get_schedule_shifts(
            claimable_by_user=self.worker.get_id())

        assert len(all_shifts) == 3
        assert len(claimable_shifts) == 2

    def test_schedule_shifts_crud_manager(self):
        self.update_permission_manager()

        all_shifts = self.schedule.get_schedule_shifts()
        claimable_shifts = self.schedule.get_schedule_shifts(
            claimable_by_user=self.worker.get_id())

        assert len(all_shifts) == 3
        assert len(claimable_shifts) == 2

    def test_schedule_shifts_crud_worker(self):
        self.update_permission_worker()

        all_shifts = self.schedule.get_schedule_shifts()
        claimable_shifts = self.schedule.get_schedule_shifts(
            claimable_by_user=self.worker.get_id())

        assert len(all_shifts) == 3
        assert len(claimable_shifts) == 2
