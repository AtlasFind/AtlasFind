import re
import unittest

from app import app
from database import transaction


class CollaborationFormTests(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True)
        self.client = app.test_client()

    def tearDown(self):
        with transaction() as connection:
            connection.execute("DELETE FROM collaboration_inquiries WHERE email='creator-test@example.com'")

    def csrf(self):
        page = self.client.get("/tr/collaborate").get_data(as_text=True)
        return re.search(r'name="csrf_token" value="([^"]+)"', page).group(1)

    def test_creator_can_submit_collaboration_request(self):
        response = self.client.post("/tr/collaborate", data={
            "csrf_token": self.csrf(), "name": "Test Creator",
            "email": "creator-test@example.com", "channel_url": "https://tiktok.com/@test",
            "inquiry_type": "creator", "message": "AtlasFind projesini incelemek ve destek olmak istiyorum.",
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Mesajın bize ulaştı", response.get_data(as_text=True))

    def test_invalid_csrf_is_rejected(self):
        response = self.client.post("/tr/collaborate", data={"csrf_token": "wrong"})
        self.assertEqual(response.status_code, 400)

    def test_admin_inquiry_page_requires_login(self):
        response = self.client.get("/admin/collaborations")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/login", response.headers["Location"])


if __name__ == "__main__":
    unittest.main()
