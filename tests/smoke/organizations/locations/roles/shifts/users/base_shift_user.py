from tests.smoke.organizations.locations.roles.shifts.base_shift import BaseShift


class BaseShiftUser(BaseShift):
    def setUp(self):
        # (if you are copying and pasting, update class title below)
        super(BaseShiftUser, self).setUp()

        # using self.unassigned_shift from BaseShift, the test will
        # make a few more workers in the role, and then fetch them
        # from the unassigned shift

        # self.worker exists from base_test.py
        # self.coworker exists from base_shift.py

        # add 3 more workers, total will now be 5

        # worker1
        self.role.create_worker(
            email="demo+coolworker@7bridg.es",
            min_hours_per_workweek=30,
            max_hours_per_workweek=40)

        # worker2
        self.role.create_worker(
            email="demo+specialworker@7bridg.es",
            min_hours_per_workweek=30,
            max_hours_per_workweek=40)

        # worker3
        self.role.create_worker(
            email="demo+amazingworker@7bridg.es",
            min_hours_per_workweek=30,
            max_hours_per_workweek=40)

        # create another shift with same time as unassigned shift
        # and assign to coworker
        self.role.create_shift(
            start=self.unassigned_shift.data.get("start"),
            stop=self.unassigned_shift.data.get("stop"),
            user_id=self.coworker.get_id())

        # there are 4 eligible workers for the unassigned shift

    def tearDown(self):
        # (if you are copying and pasting, update class title below)
        super(BaseShiftUser, self).tearDown()
