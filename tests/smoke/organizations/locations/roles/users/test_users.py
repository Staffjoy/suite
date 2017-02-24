import pytest

from tests.smoke.organizations.locations.roles.users.base_user import BaseWorker


class TestWorkers(BaseWorker):
    def setUp(self):
        # (if you are copying and pasting, update class title below)
        super(TestWorkers, self).setUp()

        # give the worker a current timeclock - this will be closed when worker
        # is removed form role
        self.open_timeclock = self.worker.create_timeclock()

    def tearDown(self):
        # (if you are copying and pasting, update class title below)
        super(TestWorkers, self).tearDown()

    def test_worker_crud_sudo(self):
        self.update_permission_sudo()

        # workers created by sudo in setup - dont need to test again

        # patch
        new_internal_id = "1337"
        self.worker.patch(internal_id=new_internal_id)
        assert self.worker.data.get("internal_id") == new_internal_id

        # other worker
        self.other_worker.patch(internal_id=new_internal_id)
        assert self.other_worker.data.get("internal_id") == new_internal_id

        # delete
        self.worker.delete()
        refetch = self.role.get_worker(self.worker.get_id())
        assert refetch.data.get("archived") is True

        # that open timeclock should be closed
        refetch_tc = self.worker.get_timeclock(self.open_timeclock.get_id())
        assert refetch_tc.data.get("stop") is not None

        self.other_worker.delete()
        refetch = self.other_role.get_worker(self.other_worker.get_id())
        assert refetch.data.get("archived") is True

    def test_worker_crud_admin(self):
        self.update_permission_admin()

        # post - access across all locations
        new_email = "demo+wassup@7bridg.es"
        new_worker = self.role.create_worker(
            email=new_email,
            min_hours_per_workweek=20,
            max_hours_per_workweek=40)
        assert new_worker.data.get("email") == new_email

        other_new_worker = self.other_role.create_worker(
            email=new_email,
            min_hours_per_workweek=20,
            max_hours_per_workweek=40)
        assert other_new_worker.data.get("email") == new_email

        # patch
        new_internal_id = "1337"
        self.worker.patch(internal_id=new_internal_id)
        assert self.worker.data.get("internal_id") == new_internal_id

        # other worker
        self.other_worker.patch(internal_id=new_internal_id)
        assert self.other_worker.data.get("internal_id") == new_internal_id

        # delete
        self.worker.delete()
        refetch = self.role.get_worker(self.worker.get_id())
        assert refetch.data.get("archived") is True

        # that open timeclock should be closed
        refetch_tc = self.worker.get_timeclock(self.open_timeclock.get_id())
        assert refetch_tc.data.get("stop") is not None

        self.other_worker.delete()
        refetch = self.other_role.get_worker(self.other_worker.get_id())
        assert refetch.data.get("archived") is True

    def test_worker_crud_manager(self):
        self.update_permission_manager()

        # post only works within managed locations
        new_email = "demo+wassup@7bridg.es"
        new_worker = self.role.create_worker(
            email=new_email,
            min_hours_per_workweek=20,
            max_hours_per_workweek=40)
        assert new_worker.data.get("email") == new_email

        with pytest.raises(Exception):
            self.other_role.create_worker(
                email=new_email,
                min_hours_per_workweek=20,
                max_hours_per_workweek=40)

        # patch
        new_internal_id = "1337"
        self.worker.patch(internal_id=new_internal_id)
        assert self.worker.data.get("internal_id") == new_internal_id

        # other worker
        with pytest.raises(Exception):
            self.other_worker.patch(internal_id=new_internal_id)

        # delete
        self.worker.delete()
        refetch = self.role.get_worker(self.worker.get_id())
        assert refetch.data.get("archived") is True

        # that open timeclock should be closed
        refetch_tc = self.worker.get_timeclock(self.open_timeclock.get_id())
        assert refetch_tc.data.get("stop") is not None

        with pytest.raises(Exception):
            self.other_worker.delete()

    def test_worker_crud_worker(self):
        self.update_permission_worker()

        # cannot add new workers
        new_email = "demo+wassup@7bridg.es"
        with pytest.raises(Exception):
            self.role.create_worker(
                email=new_email,
                min_hours_per_workweek=20,
                max_hours_per_workweek=40)

        # patch
        with pytest.raises(Exception):
            self.worker.patch(internal_id="1337")

        # delete
        with pytest.raises(Exception):
            self.worker.delete()

        # that open timeclock should not be closed
        refetch_tc = self.worker.get_timeclock(self.open_timeclock.get_id())
        assert refetch_tc.data.get("stop") is None

        with pytest.raises(Exception):
            self.other_worker.delete()
