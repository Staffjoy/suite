import pytest
from tests.smoke.organizations.locations.roles.shift_query.base_shift_query import BaseShiftQuery


class TestShifts(BaseShiftQuery):
    def setUp(self):
        # (if you are copying and pasting, update class title below)
        super(TestShifts, self).setUp()

    def tearDown(self):
        # (if you are copying and pasting, update class title below)
        super(TestShifts, self).tearDown()

    def test_shifts_crud_sudo(self):
        self.update_permission_sudo()

        # both worker and co-worker will be eligible
        eligible_workers = self.role.get_shift_query(
            start=self.query_start, stop=self.query_stop)
        assert len(eligible_workers) == 2

        # other worker will be eligible in other role
        eligible_workers = self.other_role.get_shift_query(
            start=self.query_start, stop=self.query_stop)
        assert len(eligible_workers) == 1

        # these return 400s
        # stop before start
        with pytest.raises(Exception):
            self.role.get_shift_query(
                start=self.query_stop, stop=self.query_start)

        # too long of a shift
        with pytest.raises(Exception):
            self.role.get_shift_query(
                start=self.query_start, stop=self.long_stop)

    def test_shifts_crud_admin(self):
        self.update_permission_admin()

        # both worker and co-worker will be eligible
        eligible_workers = self.role.get_shift_query(
            start=self.query_start, stop=self.query_stop)
        assert len(eligible_workers) == 2

        # other worker will be eligible in other role
        eligible_workers = self.other_role.get_shift_query(
            start=self.query_start, stop=self.query_stop)
        assert len(eligible_workers) == 1

        # these return 400s
        # stop before start
        with pytest.raises(Exception):
            self.role.get_shift_query(
                start=self.query_stop, stop=self.query_start)

        # too long of a shift
        with pytest.raises(Exception):
            self.role.get_shift_query(
                start=self.query_start, stop=self.long_stop)

    def test_shifts_crud_manager(self):
        self.update_permission_manager()

        # both worker and co-worker will be eligible
        eligible_workers = self.role.get_shift_query(
            start=self.query_start, stop=self.query_stop)
        assert len(eligible_workers) == 2

        # manager cannot query for other role
        with pytest.raises(Exception):
            self.other_role.get_shift_query(
                start=self.query_start, stop=self.query_stop)

        # these return 400s
        # stop before start
        with pytest.raises(Exception):
            self.role.get_shift_query(
                start=self.query_stop, stop=self.query_start)

        # too long of a shift
        with pytest.raises(Exception):
            self.role.get_shift_query(
                start=self.query_start, stop=self.long_stop)

    def test_shifts_crud_worker(self):
        self.update_permission_worker()

        # workers cannot do this
        with pytest.raises(Exception):
            self.role.get_shift_query(
                start=self.query_start, stop=self.query_stop)

        # or this
        with pytest.raises(Exception):
            self.other_role.get_shift_query(
                start=self.query_start, stop=self.query_stop)
