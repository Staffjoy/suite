from datetime import datetime

from app.models import Organization
from app import db
from tests.unit.test_base import BasicsTestCase


class AppTestOrganization(BasicsTestCase):
    def test_get_week_start_from_datetime(self):

        # self.organization has a day_week_start of Monday

        org2 = Organization(
            name="Test Organization",
            day_week_starts="tuesday",
            plan="per-seat-v1",
            active=True, )

        org3 = Organization(
            name="Test Organization",
            day_week_starts="wednesday",
            plan="per-seat-v1",
            active=True, )

        org4 = Organization(
            name="Test Organization",
            day_week_starts="thursday",
            plan="per-seat-v1",
            active=True, )

        org5 = Organization(
            name="Test Organization",
            day_week_starts="friday",
            plan="per-seat-v1",
            active=True, )

        org6 = Organization(
            name="Test Organization",
            day_week_starts="saturday",
            plan="per-seat-v1",
            active=True, )

        org7 = Organization(
            name="Test Organization",
            day_week_starts="sunday",
            plan="per-seat-v1",
            active=True, )

        db.session.add(org2)
        db.session.add(org3)
        db.session.add(org4)
        db.session.add(org5)
        db.session.add(org6)
        db.session.add(org7)
        db.session.commit()

        # June 21, 2016 is a Tuesday
        test_date = datetime(2016, 6, 21)

        assert self.organization.get_week_start_from_datetime(
            test_date).day == 20
        assert org2.get_week_start_from_datetime(test_date).day == 21
        assert org3.get_week_start_from_datetime(test_date).day == 15
        assert org4.get_week_start_from_datetime(test_date).day == 16
        assert org5.get_week_start_from_datetime(test_date).day == 17
        assert org6.get_week_start_from_datetime(test_date).day == 18
        assert org7.get_week_start_from_datetime(test_date).day == 19
