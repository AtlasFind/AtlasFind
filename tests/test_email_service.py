import json
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

from flask import Flask

from services.email_service import send_verification_email


class _Response:
    status = 200

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


class TransactionalEmailTests(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config.update(
            RESEND_API_KEY="re_test_key",
            RESEND_FROM="AtlasFind <hesap@updates.atlasfind.org>",
            SMTP_HOST="smtp.invalid",
            SMTP_USER="unused",
            SMTP_PASSWORD="unused",
        )

    @patch("services.email_service.urlopen", return_value=_Response())
    def test_resend_api_is_preferred_and_uses_utf8(self, mocked_urlopen):
        with self.app.app_context():
            delivered = send_verification_email(
                "uye@example.com", "Çağrı", "https://atlasfind.org/tr/verify-email?token=test", "tr"
            )

        self.assertTrue(delivered)
        request = mocked_urlopen.call_args.args[0]
        payload = json.loads(request.data.decode("utf-8"))
        self.assertEqual(payload["to"], ["uye@example.com"])
        self.assertIn("doğrula", payload["subject"])
        self.assertIn("Çağrı", payload["text"])
        self.assertEqual(request.get_header("Authorization"), "Bearer re_test_key")

    @patch("services.email_service.urlopen")
    def test_resend_api_failure_does_not_fall_back_to_blocked_smtp(self, mocked_urlopen):
        mocked_urlopen.side_effect = HTTPError(
            "https://api.resend.com/emails", 403, "Forbidden", {}, None
        )
        with self.app.app_context():
            delivered = send_verification_email(
                "uye@example.com", "uye", "https://atlasfind.org/verify-email?token=test", "tr"
            )
        self.assertFalse(delivered)


if __name__ == "__main__":
    unittest.main()
