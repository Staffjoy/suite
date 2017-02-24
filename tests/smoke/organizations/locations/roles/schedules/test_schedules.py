import json
import pytest

from tests.smoke.organizations.locations.roles.schedules.base_schedule import BaseSchedule


class TestSchedules(BaseSchedule):
    def setUp(self):
        # (if you are copying and pasting, update class title below)
        super(TestSchedules, self).setUp()

    def tearDown(self):
        # (if you are copying and pasting, update class title below)
        super(TestSchedules, self).tearDown()

    def test_schedules_crud_sudo(self):
        self.update_permission_sudo()

        # read some schedules in main role
        schedules = self.role.get_schedules(
            start=self.range_start, end=self.range_stop)
        assert 0 < len(schedules) <= 2

        # read some schedules in another role
        other_schedules = self.other_role.get_schedules(
            start=self.range_start, end=self.range_stop)
        assert 0 < len(other_schedules) <= 2

        # now some patches
        schedule = schedules.pop(0)

        # schedule starts as initial
        schedule.patch(state="unpublished")
        assert schedule.data.get("state") == "unpublished"

        # add some data to it
        schedule.patch(
            min_shift_length_hour=4,
            max_shift_length_hour=8,
            demand=json.dumps(self.demand))
        assert schedule.data.get("max_shift_length_hour") == 8
        assert schedule.data.get("min_shift_length_hour") == 4
        assert schedule.data.get("demand") == self.demand

        schedule.patch(state="published")
        assert schedule.data.get("state") == "published"

        # more schedules to test sending to different automation systems
        more_schedules = self.role.get_schedules(start=self.range_stop)
        first_schedule = more_schedules.pop(0)
        second_schedule = more_schedules.pop(0)

        first_schedule.patch(state="unpublished")
        second_schedule.patch(state="unpublished")

        first_schedule.patch(
            state="chomp-queue",
            min_shift_length_hour=4,
            max_shift_length_hour=8,
            demand=json.dumps(self.demand))
        second_schedule.patch(state="mobius-queue")

    def test_schedules_crud_admin(self):
        self.update_permission_admin()

        # read some schedules
        schedules = self.role.get_schedules(
            start=self.range_start, end=self.range_stop)
        assert 0 < len(schedules) <= 2

        # read some schedules in another role
        other_schedules = self.other_role.get_schedules(
            start=self.range_start, end=self.range_stop)
        assert 0 < len(other_schedules) <= 2

        # now some patches
        schedule = schedules.pop(0)

        # schedule starts as initial
        schedule.patch(state="unpublished")
        assert schedule.data.get("state") == "unpublished"

        # add some data to it
        schedule.patch(
            min_shift_length_hour=4,
            max_shift_length_hour=8,
            demand=json.dumps(self.demand))
        assert schedule.data.get("max_shift_length_hour") == 8
        assert schedule.data.get("min_shift_length_hour") == 4
        assert schedule.data.get("demand") == self.demand

        schedule.patch(state="published")
        assert schedule.data.get("state") == "published"

        # more schedules to test sending to different automation systems
        more_schedules = self.role.get_schedules(start=self.range_stop)
        first_schedule = more_schedules.pop(0)
        second_schedule = more_schedules.pop(0)

        first_schedule.patch(state="unpublished")
        second_schedule.patch(state="unpublished")

        first_schedule.patch(
            state="chomp-queue",
            min_shift_length_hour=4,
            max_shift_length_hour=8,
            demand=json.dumps(self.demand))
        second_schedule.patch(state="mobius-queue")

    def test_schedules_crud_manager(self):
        self.update_permission_manager()

        # read some schedules
        schedules = self.role.get_schedules(
            start=self.range_start, end=self.range_stop)
        assert 0 < len(schedules) <= 2

        with pytest.raises(Exception):
            self.other_role.get_schedules(
                start=self.range_start, end=self.range_stop)

        # now some patches
        schedule = schedules.pop(0)

        # schedule starts as initial
        schedule.patch(state="unpublished")
        assert schedule.data.get("state") == "unpublished"

        # add some data to it
        schedule.patch(
            min_shift_length_hour=4,
            max_shift_length_hour=8,
            demand=json.dumps(self.demand))
        assert schedule.data.get("max_shift_length_hour") == 8
        assert schedule.data.get("min_shift_length_hour") == 4
        assert schedule.data.get("demand") == self.demand

        schedule.patch(state="published")
        assert schedule.data.get("state") == "published"

        # more schedules to test sending to different automation systems
        more_schedules = self.role.get_schedules(start=self.range_stop)
        first_schedule = more_schedules.pop(0)
        second_schedule = more_schedules.pop(0)

        first_schedule.patch(state="unpublished")
        second_schedule.patch(state="unpublished")

        first_schedule.patch(
            state="chomp-queue",
            min_shift_length_hour=4,
            max_shift_length_hour=8,
            demand=json.dumps(self.demand))
        second_schedule.patch(state="mobius-queue")

    def test_schedules_crud_worker(self):
        self.update_permission_worker()

        # read some schedules
        schedules = self.role.get_schedules(
            start=self.range_start, end=self.range_stop)
        assert 0 < len(schedules) <= 2

        with pytest.raises(Exception):
            self.other_role.get_schedules(
                start=self.range_start, end=self.range_stop)

        # now some patches
        schedule = schedules.pop(0)

        # can't patch a schedule as a worker
        with pytest.raises(Exception):
            schedule.patch(state="unpublished")

        with pytest.raises(Exception):
            schedule.patch(
                min_shift_length_hour=4,
                max_shift_length_hour=8,
                demand=json.dumps(self.demand))
