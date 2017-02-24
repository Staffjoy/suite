from datetime import timedelta
import iso8601
from tests.smoke.organizations.locations.roles.schedules.base_schedule import BaseSchedule


class BaseScheduleShift(BaseSchedule):
    def setUp(self):
        # (if you are copying and pasting, update class title below)
        super(BaseScheduleShift, self).setUp()

        schedules = self.role.get_schedules(
            start=self.range_start, end=self.range_stop)
        self.schedule = schedules.pop()
        self.schedule.patch(state="unpublished")

        # add a worker to the role
        another_worker = self.role.create_worker(
            email="demo+anotherdude@7bridg.es",
            min_hours_per_workweek=30,
            max_hours_per_workweek=40)

        schedule_start = iso8601.parse_date(
            self.schedule.data.get("start")).replace(tzinfo=None)

        # create some shifts
        # shift data
        start1 = schedule_start + timedelta(hours=8)
        stop1 = start1 + timedelta(hours=5, minutes=30)

        start2 = schedule_start + timedelta(days=2, hours=4)
        stop2 = start2 + timedelta(hours=7)

        start3 = schedule_start + timedelta(days=4, hours=9)
        stop3 = start3 + timedelta(hours=6)

        self.role.create_shift(
            start=start1.isoformat(), stop=stop1.isoformat())
        self.role.create_shift(
            start=start2.isoformat(), stop=stop2.isoformat())
        self.role.create_shift(
            start=start3.isoformat(),
            stop=stop3.isoformat(),
            user_id=another_worker.get_id())

        self.schedule.patch(state="published")

    def tearDown(self):
        # (if you are copying and pasting, update class title below)
        super(BaseScheduleShift, self).tearDown()
