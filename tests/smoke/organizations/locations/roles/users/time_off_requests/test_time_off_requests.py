from datetime import datetime, timedelta
import pytest
import iso8601
import pytz
from app.helpers import normalize_to_midnight
from tests.smoke.organizations.locations.roles.users.time_off_requests.base_time_off_request import BaseTimeOffRequest


class TestTimeOffRequests(BaseTimeOffRequest):
    def setUp(self):
        # (if you are copying and pasting, update class title below)
        super(TestTimeOffRequests, self).setUp()

    def tearDown(self):
        # (if you are copying and pasting, update class title below)
        super(TestTimeOffRequests, self).tearDown()

    def test_time_off_request_crud_sudo(self):
        self.update_permission_sudo()

        # get
        requests = self.worker.get_time_off_requests(
            start=self.range_start, end=self.range_stop)
        assert len(requests) == 1

        # post
        today = normalize_to_midnight(datetime.utcnow())

        # create a time off request for testing against
        date1 = (today + timedelta(days=8)).strftime("%Y-%m-%d")
        date2 = (today + timedelta(days=5)).strftime("%Y-%m-%d")

        default_tz = pytz.timezone("UTC")
        local_tz = pytz.timezone(self.location.data.get("timezone"))

        # normal
        new_time_off_request = self.worker.create_time_off_request(date=date1)

        request_date = default_tz.localize(
                    iso8601.parse_date(new_time_off_request.data.get("start")
                ) \
                .replace(tzinfo=None)) \
                .astimezone(local_tz) \
                .strftime("%Y-%m-%d")

        assert request_date == date1
        assert new_time_off_request.data.get("state") is None

        # with state and hours paid
        other_time_off_request = self.other_worker.create_time_off_request(
            date=date2, minutes_paid=480, state="approved_paid")

        other_request_date = default_tz.localize(
                    iso8601.parse_date(other_time_off_request.data.get("start")
                ) \
                .replace(tzinfo=None)) \
                .astimezone(local_tz) \
                .strftime("%Y-%m-%d")

        assert other_request_date == date2
        assert other_time_off_request.data.get("minutes_paid") == 480
        assert other_time_off_request.data.get("state") == "approved_paid"

        # patch
        # respond to existing time off request
        self.time_off_request.patch(state="approved_unpaid", minute_paid=0)
        assert self.time_off_request.data.get("minutes_paid") == 0
        assert self.time_off_request.data.get("state") == "approved_unpaid"

        # modify another
        new_time_off_request.patch(state="denied", minutes_paid=0)
        assert new_time_off_request.data.get("minutes_paid") == 0
        assert new_time_off_request.data.get("state") == "denied"

        # and in other worker/role
        other_time_off_request.patch(state="approved_paid", minutes_paid=360)
        assert other_time_off_request.data.get("minutes_paid") == 360
        assert other_time_off_request.data.get("state") == "approved_paid"

        # delete
        self.time_off_request.delete()
        new_time_off_request.delete()
        other_time_off_request.delete()

        with pytest.raises(Exception):
            self.worker.get_time_off_request(self.time_off_request.get_id())

        with pytest.raises(Exception):
            self.worker.get_time_off_request(new_time_off_request.get_id())

        with pytest.raises(Exception):
            self.other_worker.get_time_off_request(
                other_time_off_request.get_id())

    def test_time_off_request_crud_admin(self):
        self.update_permission_admin()

        # get
        requests = self.worker.get_time_off_requests(
            start=self.range_start, end=self.range_stop)
        assert len(requests) == 1

        # post
        today = normalize_to_midnight(datetime.utcnow())

        # create a time off request for testing against
        date1 = (today + timedelta(days=8)).strftime("%Y-%m-%d")
        date2 = (today + timedelta(days=5)).strftime("%Y-%m-%d")

        default_tz = pytz.timezone("UTC")
        local_tz = pytz.timezone(self.location.data.get("timezone"))

        # normal
        new_time_off_request = self.worker.create_time_off_request(date=date1)

        request_date = default_tz.localize(
                    iso8601.parse_date(new_time_off_request.data.get("start")
                ) \
                .replace(tzinfo=None)) \
                .astimezone(local_tz) \
                .strftime("%Y-%m-%d")

        assert request_date == date1
        assert new_time_off_request.data.get("state") is None

        # with state and hours paid
        other_time_off_request = self.other_worker.create_time_off_request(
            date=date2, minutes_paid=480, state="approved_paid")

        other_request_date = default_tz.localize(
                    iso8601.parse_date(other_time_off_request.data.get("start")
                ) \
                .replace(tzinfo=None)) \
                .astimezone(local_tz) \
                .strftime("%Y-%m-%d")

        assert other_request_date == date2
        assert other_time_off_request.data.get("minutes_paid") == 480
        assert other_time_off_request.data.get("state") == "approved_paid"

        # patch
        # respond to existing time off request
        self.time_off_request.patch(state="approved_unpaid", minute_paid=0)
        assert self.time_off_request.data.get("minutes_paid") == 0
        assert self.time_off_request.data.get("state") == "approved_unpaid"

        # modify another
        new_time_off_request.patch(state="denied", minutes_paid=0)
        assert new_time_off_request.data.get("minutes_paid") == 0
        assert new_time_off_request.data.get("state") == "denied"

        # and in other worker/role
        other_time_off_request.patch(state="approved_paid", minutes_paid=360)
        assert other_time_off_request.data.get("minutes_paid") == 360
        assert other_time_off_request.data.get("state") == "approved_paid"

        # delete
        self.time_off_request.delete()
        new_time_off_request.delete()
        other_time_off_request.delete()

        with pytest.raises(Exception):
            self.worker.get_time_off_request(self.time_off_request.get_id())

        with pytest.raises(Exception):
            self.worker.get_time_off_request(new_time_off_request.get_id())

        with pytest.raises(Exception):
            self.other_worker.get_time_off_request(
                other_time_off_request.get_id())

    def test_time_off_request_crud_manager(self):
        self.update_permission_manager()

        # get
        requests = self.worker.get_time_off_requests(
            start=self.range_start, end=self.range_stop)
        assert len(requests) == 1

        # post
        today = normalize_to_midnight(datetime.utcnow())

        # create a time off request for testing against
        date1 = (today + timedelta(days=8)).strftime("%Y-%m-%d")
        date2 = (today + timedelta(days=5)).strftime("%Y-%m-%d")

        default_tz = pytz.timezone("UTC")
        local_tz = pytz.timezone(self.location.data.get("timezone"))

        # normal
        new_time_off_request = self.worker.create_time_off_request(
            date=date1, minutes_paid=480, state="approved_paid")

        request_date = default_tz.localize(
                    iso8601.parse_date(new_time_off_request.data.get("start")
                ) \
                .replace(tzinfo=None)) \
                .astimezone(local_tz) \
                .strftime("%Y-%m-%d")

        assert request_date == date1
        assert new_time_off_request.data.get("minutes_paid") == 480
        assert new_time_off_request.data.get("state") == "approved_paid"

        # other roles fail for managers
        with pytest.raises(Exception):
            self.other_worker.create_time_off_request(
                date=date2, minutes_paid=0, state="approved_unpaid")

        # patch
        # respond to existing time off request
        self.time_off_request.patch(state="approved_unpaid", minute_paid=0)
        assert self.time_off_request.data.get("minutes_paid") == 0
        assert self.time_off_request.data.get("state") == "approved_unpaid"

        # modify another
        new_time_off_request.patch(state="denied", minutes_paid=0)
        assert new_time_off_request.data.get("minutes_paid") == 0
        assert new_time_off_request.data.get("state") == "denied"

        # delete
        self.time_off_request.delete()
        new_time_off_request.delete()

        with pytest.raises(Exception):
            self.worker.get_time_off_request(self.time_off_request.get_id())

        with pytest.raises(Exception):
            self.worker.get_time_off_request(new_time_off_request.get_id())

    def test_time_off_request_crud_worker(self):
        self.update_permission_worker()

        # get
        requests = self.worker.get_time_off_requests(
            start=self.range_start, end=self.range_stop)
        assert len(requests) == 1

        # post
        today = normalize_to_midnight(datetime.utcnow())

        # create a time off request for testing against
        date1 = (today + timedelta(days=8)).strftime("%Y-%m-%d")
        date2 = (today + timedelta(days=5)).strftime("%Y-%m-%d")

        default_tz = pytz.timezone("UTC")
        local_tz = pytz.timezone(self.location.data.get("timezone"))

        # can request on a date, but state needs to be left alone
        new_time_off_request = self.worker.create_time_off_request(date=date1)

        request_date = default_tz.localize(
                    iso8601.parse_date(new_time_off_request.data.get("start")
                ) \
                .replace(tzinfo=None)) \
                .astimezone(local_tz) \
                .strftime("%Y-%m-%d")

        assert request_date == date1
        assert new_time_off_request.data.get("state") is None

        # cannot request with it defined
        with pytest.raises(Exception):
            self.worker.create_time_off_request(
                date=date2, minutes_paid=480, state="approved_paid")

        # patch
        # not allowed
        with pytest.raises(Exception):
            self.time_off_request.patch(state="approved_paid", minute_paid=480)

        with pytest.raises(Exception):
            new_time_off_request.patch(state="denied", minutes_paid=0)

        # delete
        new_time_off_request.delete()

        # can delete an unresolved request
        with pytest.raises(Exception):
            self.worker.get_time_off_request(new_time_off_request.get_id())

        # cannot delete once manager has touched it
        self.update_permission_manager()
        self.time_off_request.patch(state="approved_paid", minutes_paid=300)
        self.update_permission_worker()

        with pytest.raises(Exception):
            self.time_off_request.delete()
