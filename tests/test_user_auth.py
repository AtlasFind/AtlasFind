import re
import unittest
from unittest.mock import patch
from urllib.parse import urlsplit

from app import app
from database import connect_database, transaction
from security import user_auth_limiter


TEST_EMAIL = "auth-user-test@example.com"
TEST_USERNAME = "auth_user_test"
TEST_PASSWORD = "SecurePass123"


class UserAuthTests(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True)
        with user_auth_limiter._lock:
            user_auth_limiter._events.clear()
        self.client = app.test_client()
        self.cleanup()

    def tearDown(self):
        self.cleanup()

    def cleanup(self):
        with transaction() as connection:
            connection.execute("DELETE FROM user_login_attempts WHERE identity IN (?,?)", (TEST_EMAIL, TEST_USERNAME))
            connection.execute("DELETE FROM user_favorites WHERE user_id IN (SELECT id FROM user_accounts WHERE email=? OR username=?)", (TEST_EMAIL, TEST_USERNAME))
            connection.execute("DELETE FROM user_accounts WHERE email=? OR username=?", (TEST_EMAIL, TEST_USERNAME))

    @staticmethod
    def token(page):
        return re.search(r'name="csrf_token" value="([^"]+)"', page).group(1)

    def register(self):
        page = self.client.get("/tr/register").get_data(as_text=True)
        with patch("app.send_verification_email", return_value=True) as sender:
            response = self.client.post("/tr/register", data={
                "csrf_token": self.token(page), "username": TEST_USERNAME,
                "email": TEST_EMAIL, "password": TEST_PASSWORD,
                "confirm_password": TEST_PASSWORD, "accept_terms": "1",
            }, follow_redirects=True)
        return response, sender.call_args.args[2]

    def verify(self, url):
        parts = urlsplit(url)
        return self.client.get(parts.path + "?" + parts.query, follow_redirects=True)

    def test_register_requires_email_verification_and_hashes_password(self):
        response, verification_url = self.register()
        self.assertEqual(response.status_code, 200)
        self.assertIn("auth.css?v=1.4.0", response.get_data(as_text=True))
        with connect_database() as connection:
            row = connection.execute("SELECT * FROM user_accounts WHERE email=?", (TEST_EMAIL,)).fetchone()
        self.assertNotEqual(row["password_hash"], TEST_PASSWORD)
        self.assertEqual(row["email_verified"], 0)
        self.assertTrue(row["verification_token_hash"])
        verified = self.verify(verification_url)
        self.assertIn(TEST_USERNAME, verified.get_data(as_text=True))
        with connect_database() as connection:
            row = connection.execute("SELECT email_verified FROM user_accounts WHERE email=?", (TEST_EMAIL,)).fetchone()
        self.assertEqual(row["email_verified"], 1)

    def test_unverified_account_cannot_login(self):
        self.register()
        login_page = self.client.get("/tr/login").get_data(as_text=True)
        response = self.client.post("/tr/login", data={
            "csrf_token": self.token(login_page), "identity": TEST_EMAIL,
            "password": TEST_PASSWORD,
        }, follow_redirects=True)
        self.assertIn("doğrulamalısın", response.get_data(as_text=True))

    def test_verified_user_login_checks_registered_password(self):
        _, verification_url = self.register()
        profile = self.verify(verification_url).get_data(as_text=True)
        self.client.post("/tr/logout", data={"csrf_token": self.token(profile)})
        login_page = self.client.get("/tr/login").get_data(as_text=True)
        bad = self.client.post("/tr/login", data={"csrf_token": self.token(login_page), "identity": TEST_USERNAME, "password": "WrongPassword1"}, follow_redirects=True)
        self.assertNotIn(TEST_USERNAME, bad.get_data(as_text=True))
        login_page = self.client.get("/tr/login").get_data(as_text=True)
        good = self.client.post("/tr/login", data={"csrf_token": self.token(login_page), "identity": TEST_USERNAME, "password": TEST_PASSWORD}, follow_redirects=True)
        self.assertIn(TEST_USERNAME, good.get_data(as_text=True))

    def test_invalid_verification_link_and_csrf_are_rejected(self):
        self.register()
        response = self.client.get("/tr/verify-email?token=wrong", follow_redirects=True)
        self.assertIn("geçersiz", response.get_data(as_text=True))
        response = self.client.post("/tr/register", data={"csrf_token": "invalid"})
        self.assertEqual(response.status_code, 400)

    def test_different_passwords_never_create_an_account(self):
        page = self.client.get("/tr/register").get_data(as_text=True)
        response = self.client.post("/tr/register", data={
            "csrf_token": self.token(page), "username": TEST_USERNAME,
            "email": TEST_EMAIL, "password": TEST_PASSWORD,
            "confirm_password": "AnotherPass456", "accept_terms": "1",
        }, follow_redirects=True)
        self.assertIn("eşleşmiyor", response.get_data(as_text=True))
        with connect_database() as connection:
            row = connection.execute("SELECT id FROM user_accounts WHERE email=?", (TEST_EMAIL,)).fetchone()
        self.assertIsNone(row)

    def test_wrong_email_cannot_open_an_existing_account(self):
        _, verification_url = self.register()
        profile = self.verify(verification_url).get_data(as_text=True)
        self.client.post("/tr/logout", data={"csrf_token": self.token(profile)})
        login_page = self.client.get("/tr/login").get_data(as_text=True)
        response = self.client.post("/tr/login", data={
            "csrf_token": self.token(login_page), "identity": "wrong@example.com",
            "password": TEST_PASSWORD,
        }, follow_redirects=True)
        self.assertIn("hatalı", response.get_data(as_text=True))
        self.assertNotIn(TEST_USERNAME, response.get_data(as_text=True))

    def test_profile_details_and_password_can_be_updated_securely(self):
        _, verification_url = self.register()
        profile = self.verify(verification_url).get_data(as_text=True)
        updated = self.client.post("/tr/profile", data={
            "csrf_token": self.token(profile), "action": "profile",
            "display_name": "Atlas Tester", "bio": "Araçları güvenle test eder.",
            "country": "Türkiye", "website_url": "https://example.com",
            "profile_visibility": "public",
        }, follow_redirects=True)
        body = updated.get_data(as_text=True)
        self.assertIn("Atlas Tester", body)
        self.assertIn("Araçları güvenle test eder", body)
        changed = self.client.post("/tr/profile", data={
            "csrf_token": self.token(body), "action": "password",
            "current_password": TEST_PASSWORD, "new_password": "NewSecurePass456",
            "confirm_new_password": "NewSecurePass456",
        }, follow_redirects=True)
        self.assertIn("güvenli biçimde değiştirildi", changed.get_data(as_text=True))
        with connect_database() as connection:
            row = connection.execute("SELECT display_name,profile_visibility FROM user_accounts WHERE email=?", (TEST_EMAIL,)).fetchone()
        self.assertEqual(row["display_name"], "Atlas Tester")
        self.assertEqual(row["profile_visibility"], "public")

    def test_verified_user_can_save_and_remove_a_tool(self):
        _, verification_url = self.register()
        profile = self.verify(verification_url).get_data(as_text=True)
        self.client.post("/tr/tools/chatgpt/favorite", data={
            "csrf_token": self.token(profile), "saved": "1",
        }, follow_redirects=True)
        profile = self.client.get("/tr/profile").get_data(as_text=True)
        self.assertIn("ChatGPT", profile)
        self.client.post("/tr/tools/chatgpt/favorite", data={
            "csrf_token": self.token(profile), "saved": "0",
        }, follow_redirects=True)
        profile = self.client.get("/tr/profile").get_data(as_text=True)
        self.assertNotIn("tool-bag-main\" href=\"/tr/tools/chatgpt", profile)


if __name__ == "__main__":
    unittest.main()
