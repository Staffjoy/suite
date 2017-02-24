from datetime import datetime, timedelta
import pytest
from tests.smoke.organizations.locations.roles.users.timeclocks.base_timeclock import BaseTimeclock


class TestTimeclocks(BaseTimeclock):
    def setUp(self):
        # (if you are copying and pasting, update class title below)
        super(TestTimeclocks, self).setUp()

    def tearDown(self):
        # (if you are copying and pasting, update class title below)
        super(TestTimeclocks, self).tearDown()

    def test_timeclock_crud_sudo(self):
        self.update_permission_sudo()

        # posts
        # clock the worker in
        timeclock = self.worker.create_timeclock()
        assert timeclock.data.get("start") is not None
        assert timeclock.data.get("stop") is None

        # cannot clock in twice
        with pytest.raises(Exception):
            self.worker.create_timeclock()

        # manager cannot clock in workers at other locations
        other_timeclock = self.other_worker.create_timeclock()
        assert other_timeclock.data.get("start") is not None
        assert other_timeclock.data.get("stop") is None

        # manager can create a complete timeclock
        start_dt = (datetime.utcnow() - timedelta(days=1)).replace(
            microsecond=0)
        start = start_dt.isoformat()
        stop = (start_dt + timedelta(hours=6, minutes=15)).isoformat()
        timeclock2 = self.worker.create_timeclock(start=start, stop=stop)
        assert timeclock2.data.get("start") == start
        assert timeclock2.data.get("stop") == stop

        # cannot create a timeclock in the future
        utcnow = datetime.utcnow()
        start_future = (utcnow + timedelta(hours=1)).isoformat()
        stop_future = (utcnow + timedelta(hours=9)).isoformat()
        with pytest.raises(Exception):
            self.worker.create_timeclock(start=start_future, stop=stop_future)

        # get
        active_timeclocks = self.worker.get_timeclocks(active=True)
        assert len(active_timeclocks) == 1

        # patch
        timeclock.patch(close=True)
        assert timeclock.data.get("stop") is not None

        new_start = (
            datetime.utcnow() - timedelta(hours=4, minutes=8)).replace(
                microsecond=0).isoformat()
        timeclock.patch(start=new_start)
        assert timeclock.data.get("start") == new_start

        # mixed parameters needs to fail
        with pytest.raises(Exception):
            timeclock.patch(start=new_start, close=True)

        # cannot modify timeclock to be in the future
        with pytest.raises(Exception):
            timeclock.patch(start=start_future, stop=stop_future)

        # delete
        timeclock.delete()
        with pytest.raises(Exception):
            self.worker.get_timeclock(timeclock.get_id())

    def test_timeclock_crud_admin(self):
        self.update_permission_admin()

        # posts
        # clock the worker in
        timeclock = self.worker.create_timeclock()
        assert timeclock.data.get("start") is not None
        assert timeclock.data.get("stop") is None

        # cannot clock in twice
        with pytest.raises(Exception):
            self.worker.create_timeclock()

        # admin can clock in workers at other locations
        other_timeclock = self.other_worker.create_timeclock()
        assert other_timeclock.data.get("start") is not None
        assert other_timeclock.data.get("stop") is None

        # admin can create a complete timeclock
        start_dt = (datetime.utcnow() - timedelta(days=1)).replace(
            microsecond=0)
        start = start_dt.isoformat()
        stop = (start_dt + timedelta(hours=6, minutes=15)).isoformat()
        timeclock2 = self.worker.create_timeclock(start=start, stop=stop)
        assert timeclock2.data.get("start") == start
        assert timeclock2.data.get("stop") == stop

        # cannot create a timeclock in the future
        utcnow = datetime.utcnow()
        start_future = (utcnow + timedelta(hours=1)).isoformat()
        stop_future = (utcnow + timedelta(hours=9)).isoformat()
        with pytest.raises(Exception):
            self.worker.create_timeclock(start=start_future, stop=stop_future)

        # get
        active_timeclocks = self.worker.get_timeclocks(active=True)
        assert len(active_timeclocks) == 1

        # patch
        timeclock.patch(close=True)
        assert timeclock.data.get("stop") is not None

        new_start = (
            datetime.utcnow() - timedelta(hours=4, minutes=8)).replace(
                microsecond=0).isoformat()
        timeclock.patch(start=new_start)
        assert timeclock.data.get("start") == new_start

        # mixed parameters needs to fail
        with pytest.raises(Exception):
            timeclock.patch(start=new_start, close=True)

        # cannot modify timeclock to be in the future
        with pytest.raises(Exception):
            timeclock.patch(start=start_future, stop=stop_future)

        # delete
        timeclock.delete()
        with pytest.raises(Exception):
            self.worker.get_timeclock(timeclock.get_id())

    def test_timeclock_crud_manager(self):
        self.update_permission_manager()

        # posts
        # clock the worker in
        timeclock = self.worker.create_timeclock()
        assert timeclock.data.get("start") is not None
        assert timeclock.data.get("stop") is None

        # cannot clock in twice
        with pytest.raises(Exception):
            self.worker.create_timeclock()

        # manager cannot clock in workers at other locations
        with pytest.raises(Exception):
            self.other_worker.create_timeclock()

        # manager can create a complete timeclock
        start_dt = (datetime.utcnow() - timedelta(days=1)).replace(
            microsecond=0)
        start = start_dt.isoformat()
        stop = (start_dt + timedelta(hours=6, minutes=15)).isoformat()
        timeclock2 = self.worker.create_timeclock(start=start, stop=stop)
        assert timeclock2.data.get("start") == start
        assert timeclock2.data.get("stop") == stop

        # cannot create a timeclock in the future
        utcnow = datetime.utcnow()
        start_future = (utcnow + timedelta(hours=1)).isoformat()
        stop_future = (utcnow + timedelta(hours=9)).isoformat()
        with pytest.raises(Exception):
            self.worker.create_timeclock(start=start_future, stop=stop_future)

        # get
        active_timeclocks = self.worker.get_timeclocks(active=True)
        assert len(active_timeclocks) == 1

        # patch
        timeclock.patch(close=True)
        assert timeclock.data.get("stop") is not None

        new_start = (
            datetime.utcnow() - timedelta(hours=4, minutes=8)).replace(
                microsecond=0).isoformat()
        timeclock.patch(start=new_start)
        assert timeclock.data.get("start") == new_start

        # mixed parameters needs to fail
        with pytest.raises(Exception):
            timeclock.patch(start=new_start, close=True)

        # cannot modify timeclock to be in the future
        with pytest.raises(Exception):
            timeclock.patch(start=start_future, stop=stop_future)

        # delete
        timeclock.delete()
        with pytest.raises(Exception):
            self.worker.get_timeclock(timeclock.get_id())

    def test_timeclock_crud_worker(self):
        self.update_permission_worker()

        # posts
        # worker clocks in
        timeclock = self.worker.create_timeclock()
        assert timeclock.data.get("start") is not None
        assert timeclock.data.get("stop") is None

        # cannot clock in twice
        with pytest.raises(Exception):
            self.worker.create_timeclock()

        # worker cannot clock in a buddy
        with pytest.raises(Exception):
            self.other_worker.create_timeclock()

        # worker cannot make a complete timeclock
        start_dt = (datetime.utcnow() - timedelta(days=1)).replace(
            microsecond=0)
        start = start_dt.isoformat()
        stop = (start_dt + timedelta(hours=6, minutes=15)).isoformat()
        with pytest.raises(Exception):
            self.worker.create_timeclock(start=start, stop=stop)

        # get
        active_timeclocks = self.worker.get_timeclocks(active=True)
        assert len(active_timeclocks) == 1

        # patch
        # can only pass close=true param
        timeclock.patch(close=True)
        assert timeclock.data.get("stop") is not None

        # cannot adjust start or stop
        with pytest.raises(Exception):
            timeclock.patch(start=start, stop=stop)

        # mixed parameters needs to fail
        with pytest.raises(Exception):
            timeclock.patch(start=start, close=True)

        # delete
        with pytest.raises(Exception):
            timeclock.delete()
