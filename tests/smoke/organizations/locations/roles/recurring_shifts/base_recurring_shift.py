from tests.smoke.organizations.locations.roles.base_role import BaseRole


class BaseRecurringShift(BaseRole):
    def setUp(self):
        # (if you are copying and pasting, update class title below)
        super(BaseRecurringShift, self).setUp()

        self.recurring_shift = self.role.create_recurring_shift(
            start_day="monday",
            start_hour=8,
            start_minute=0,
            duration_minutes=300,
            user_id=self.worker.get_id())

        self.other_recurring_shift = self.other_role.create_recurring_shift(
            start_day="monday",
            start_hour=8,
            start_minute=0,
            duration_minutes=300, )

    def tearDown(self):
        # (if you are copying and pasting, update class title below)
        super(BaseRecurringShift, self).tearDown()
