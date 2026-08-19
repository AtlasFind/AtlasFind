import unittest

from flask import g

from app import app
from i18n import get_locale


class LocaleRuntimeTests(unittest.TestCase):
    def test_get_locale_safely_defaults_outside_request_context(self):
        self.assertEqual(get_locale(), "en")

    def test_get_locale_reads_resolved_request_locale(self):
        with app.test_request_context("/tr/"):
            g.locale = "tr"
            self.assertEqual(get_locale(), "tr")


if __name__ == "__main__":
    unittest.main()
