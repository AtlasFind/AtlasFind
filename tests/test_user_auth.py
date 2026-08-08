import re
import unittest

from app import app
from database import connect_database, transaction


TEST_EMAIL = "auth-user-test@example.com"
TEST_USERNAME = "auth_user_test"
TEST_PASSWORD = "SecurePass123"


class UserAuthTests(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True)
        self.client = app.test_client()
        self.cleanup()

    def tearDown(self):
        self.cleanup()

    def cleanup(self):
        with transaction() as connection:
            connection.execute("DELETE FROM user_login_attempts WHERE identity IN (?,?)", (TEST_EMAIL, TEST_USERNAME))
            connection.execute("DELETE FROM user_accounts WHERE email=? OR username=?", (TEST_EMAIL, TEST_USERNAME))

    @staticmethod
    def token(page):
        return re.search(r'name="csrf_token" value="([^"]+)"', page).group(1)

    def register(self):
        page = self.client.get("/tr/register").get_data(as_text=True)
        return self.client.post("/tr/register", data={
            "csrf_token": self.token(page), "username": TEST_USERNAME,
            "email": TEST_EMAIL, "password": TEST_PASSWORD,
            "confirm_password": TEST_PASSWORD, "accept_terms": "1",
        }, follow_redirects=True)

    def test_register_creates_hashed_account_and_profile_session(self):
        response = self.register()
        self.assertEqual(response.status_code, 200)
        self.assertIn("Hesabın başarıyla oluşturuldu", response.get_data(as_text=True))
        with connect_database() as connection:
            row = connection.execute("SELECT * FROM user_accounts WHERE email=?", (TEST_EMAIL,)).fetchone()
        self.assertIsNotNone(row)
        self.assertNotEqual(row["password_hash"], TEST_PASSWORD)
        self.assertTrue(row["password_hash"].startswith(("scrypt:", "pbkdf2:")))

    def test_logout_and_login_with_email(self):
        self.register()
        profile = self.client.get("/tr/profile").get_data(as_text=True)
        self.client.post("/tr/logout", data={"csrf_token": self.token(profile)})
        login_page = self.client.get("/tr/login").get_data(as_text=True)
        response = self.client.post("/tr/login", data={
            "csrf_token": self.token(login_page), "identity": TEST_EMAIL,
            "password": TEST_PASSWORD,
        }, follow_redirects=True)
        self.assertIn(TEST_USERNAME, response.get_data(as_text=True))

    def test_profile_requires_login_and_csrf_is_enforced(self):
        response = self.client.get("/tr/profile")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/tr/login", response.headers["Location"])
        response = self.client.post("/tr/register", data={"csrf_token": "invalid"})
        self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main()
