import re
import unittest
from unittest.mock import patch

from app import app
from database import transaction


class CollaborationFormTests(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True)
        self.client = app.test_client()

    def tearDown(self):
        with transaction() as connection:
            connection.execute(
                "DELETE FROM collaboration_inquiries WHERE email IN ('creator-test@example.com','feedback-test@example.com')"
            )

    def csrf(self):
        page = self.client.get("/tr/collaborate").get_data(as_text=True)
        return re.search(r'name="csrf_token" value="([^"]+)"', page).group(1)

    @patch("app.send_inquiry_notification", return_value=True)
    def test_creator_can_submit_collaboration_request(self, notification):
        response = self.client.post(
            "/tr/collaborate",
            data={
                "csrf_token": self.csrf(), "name": "Test Creator",
                "email": "creator-test@example.com", "channel_url": "https://tiktok.com/@test",
                "inquiry_type": "creator", "message": "AtlasFind projesini incelemek ve destek olmak istiyorum.",
            },
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("Mesajın bize ulaştı", response.get_data(as_text=True))
        notification.assert_called_once()
        self.assertEqual(notification.call_args.args[0], "atlasfindd@gmail.com")
        self.assertEqual(notification.call_args.args[3], "creator-test@example.com")

    @patch("app.send_inquiry_notification", return_value=True)
    def test_contact_page_collects_feedback_and_sends_notification(self, notification):
        page = self.client.get("/tr/contact").get_data(as_text=True)
        token = re.search(r'name="csrf_token" value="([^"]+)"', page).group(1)
        self.assertIn('value="feedback" selected', page)

        response = self.client.post(
            "/tr/contact",
            data={
                "csrf_token": token, "name": "Test Visitor",
                "email": "feedback-test@example.com", "channel_url": "",
                "inquiry_type": "feedback", "message": "Arama sonuçları sayfasında bir hata fark ettim.",
            },
            follow_redirects=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("Mesajın bize ulaştı", response.get_data(as_text=True))
        notification.assert_called_once()
        self.assertEqual(notification.call_args.args[5], "feedback")

    @patch("app.send_inquiry_notification", return_value=False)
    def test_saved_request_still_succeeds_when_email_provider_is_temporarily_down(self, notification):
        response = self.client.post(
            "/tr/collaborate",
            data={
                "csrf_token": self.csrf(), "name": "Test Creator",
                "email": "creator-test@example.com", "channel_url": "",
                "inquiry_type": "other", "message": "Bu mesaj veritabanında güvenli şekilde kalmalıdır.",
            },
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("Mesajın bize ulaştı", response.get_data(as_text=True))
        notification.assert_called_once()

    def test_invalid_csrf_is_rejected(self):
        response = self.client.post("/tr/collaborate", data={"csrf_token": "wrong"})
        self.assertEqual(response.status_code, 400)

    def test_admin_inquiry_page_requires_login(self):
        response = self.client.get("/admin/collaborations")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/login", response.headers["Location"])


if __name__ == "__main__":
    unittest.main()
