from flask import current_app
from tests.unit.test_base import BasicsTestCase


class AppTestCase(BasicsTestCase):
    def test_app_exists(self):
        self.assertFalse(current_app is None)
