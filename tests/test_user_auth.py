import re
import unittest
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

from app import APP_VERSION, app
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
        self.deleted_user_id = None
        self.cleanup()

    def tearDown(self):
        self.cleanup()

    def cleanup(self):
        with transaction() as connection:
            connection.execute("DELETE FROM user_login_attempts WHERE identity IN (?,?)", (TEST_EMAIL, TEST_USERNAME))
            connection.execute("DELETE FROM user_favorites WHERE user_id IN (SELECT id FROM user_accounts WHERE email=? OR username=?)", (TEST_EMAIL, TEST_USERNAME))
            connection.execute("DELETE FROM user_accounts WHERE email=? OR username=?", (TEST_EMAIL, TEST_USERNAME))
            if self.deleted_user_id:
                connection.execute("DELETE FROM user_accounts WHERE id=?", (self.deleted_user_id,))

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
        confirmation_url = parts.path + "?" + parts.query
        confirmation = self.client.get(confirmation_url)
        return self.client.post(
            confirmation_url,
            data={"csrf_token": self.token(confirmation.get_data(as_text=True))},
            follow_redirects=True,
        )

    def test_register_requires_email_verification_and_hashes_password(self):
        response, verification_url = self.register()
        self.assertEqual(response.status_code, 200)
        self.assertIn(f"auth.css?v={APP_VERSION}", response.get_data(as_text=True))
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

    def test_email_link_preview_does_not_consume_verification_token(self):
        _, verification_url = self.register()
        parts = urlsplit(verification_url)
        preview = self.client.get(parts.path + "?" + parts.query)
        self.assertEqual(preview.status_code, 200)
        self.assertIn('method="post"', preview.get_data(as_text=True))
        with connect_database() as connection:
            row = connection.execute(
                "SELECT email_verified,verification_token_hash FROM user_accounts WHERE email=?",
                (TEST_EMAIL,),
            ).fetchone()
        self.assertEqual(row["email_verified"], 0)
        self.assertTrue(row["verification_token_hash"])

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

    def test_login_returns_user_to_safe_requested_page(self):
        _, verification_url = self.register()
        profile = self.verify(verification_url).get_data(as_text=True)
        self.client.post("/tr/logout", data={"csrf_token": self.token(profile)})
        login_page = self.client.get("/tr/login?next=/tr/tools/chatgpt").get_data(as_text=True)
        response = self.client.post("/tr/login", data={
            "csrf_token": self.token(login_page), "next": "/tr/tools/chatgpt",
            "identity": TEST_EMAIL, "password": TEST_PASSWORD,
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.headers["Location"].endswith("/tr/tools/chatgpt"))

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

    def test_password_reset_is_single_use_and_changes_login_password(self):
        _, verification_url = self.register()
        self.verify(verification_url)
        with self.client.session_transaction() as session_data:
            session_data.clear()
        page = self.client.get("/tr/forgot-password").get_data(as_text=True)
        with patch("app.send_password_reset_email", return_value=True) as sender:
            response = self.client.post("/tr/forgot-password", data={
                "csrf_token": self.token(page), "email": TEST_EMAIL,
            }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        reset_url = sender.call_args.args[2]
        parts = urlsplit(reset_url)
        token = parse_qs(parts.query)["token"][0]
        reset_page = self.client.get(parts.path + "?" + parts.query).get_data(as_text=True)
        changed = self.client.post(parts.path, data={
            "csrf_token": self.token(reset_page), "token": token,
            "password": "ReplacementPass456", "confirm_password": "ReplacementPass456",
        }, follow_redirects=True)
        self.assertEqual(changed.status_code, 200)
        reused_page = self.client.get(parts.path + "?" + parts.query).get_data(as_text=True)
        reused = self.client.post(parts.path, data={
            "csrf_token": self.token(reused_page), "token": token,
            "password": "AnotherValidPass789", "confirm_password": "AnotherValidPass789",
        }, follow_redirects=True)
        self.assertIn("geçersiz", reused.get_data(as_text=True).lower())
        login_page = self.client.get("/tr/login").get_data(as_text=True)
        old_login = self.client.post("/tr/login", data={
            "csrf_token": self.token(login_page), "identity": TEST_EMAIL, "password": TEST_PASSWORD,
        }, follow_redirects=True)
        self.assertIn("hatalı", old_login.get_data(as_text=True).lower())
        login_page = self.client.get("/tr/login").get_data(as_text=True)
        new_login = self.client.post("/tr/login", data={
            "csrf_token": self.token(login_page), "identity": TEST_EMAIL, "password": "ReplacementPass456",
        }, follow_redirects=True)
        self.assertIn(TEST_USERNAME, new_login.get_data(as_text=True))

    def test_password_reset_does_not_reveal_unknown_email(self):
        page = self.client.get("/tr/forgot-password").get_data(as_text=True)
        with patch("app.send_password_reset_email") as sender:
            response = self.client.post("/tr/forgot-password", data={
                "csrf_token": self.token(page), "email": "unknown-account@example.com",
            }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(sender.called)
        self.assertIn("kayıtlıysa", response.get_data(as_text=True).lower())

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

    def test_only_public_verified_profiles_are_shareable(self):
        _, verification_url = self.register()
        profile = self.verify(verification_url).get_data(as_text=True)
        self.client.post("/tr/profile", data={
            "csrf_token": self.token(profile), "action": "profile",
            "display_name": "Public Atlas", "bio": "Paylaşılan profil",
            "country": "Türkiye", "website_url": "", "profile_visibility": "public",
        }, follow_redirects=True)
        profile = self.client.get("/tr/profile").get_data(as_text=True)
        self.client.post("/tr/tools/chatgpt/favorite", data={"csrf_token": self.token(profile), "saved": "1"})
        public = self.client.get(f"/tr/u/{TEST_USERNAME}")
        body = public.get_data(as_text=True)
        self.assertEqual(public.status_code, 200)
        self.assertIn("Public Atlas", body)
        self.assertIn("ChatGPT", body)
        self.assertNotIn(TEST_EMAIL, body)
        profile = self.client.get("/tr/profile").get_data(as_text=True)
        self.client.post("/tr/profile", data={
            "csrf_token": self.token(profile), "action": "profile",
            "display_name": "Public Atlas", "bio": "", "country": "",
            "website_url": "", "profile_visibility": "private",
        })
        self.assertEqual(self.client.get(f"/tr/u/{TEST_USERNAME}").status_code, 404)

    def test_account_export_excludes_secrets_and_deletion_anonymizes_data(self):
        _, verification_url = self.register()
        with connect_database() as connection:
            self.deleted_user_id = connection.execute("SELECT id FROM user_accounts WHERE email=?", (TEST_EMAIL,)).fetchone()["id"]
        profile = self.verify(verification_url).get_data(as_text=True)
        self.client.post("/tr/tools/chatgpt/favorite", data={"csrf_token": self.token(profile), "saved": "1"})
        exported = self.client.get("/tr/account/export")
        self.assertEqual(exported.status_code, 200)
        self.assertIn("attachment", exported.headers["Content-Disposition"])
        payload = exported.get_json()
        self.assertEqual(payload["atlasfind_account"]["email"], TEST_EMAIL)
        self.assertEqual(payload["saved_tools"][0]["tool_slug"], "chatgpt")
        self.assertNotIn("password", exported.get_data(as_text=True).lower())
        profile = self.client.get("/tr/profile").get_data(as_text=True)
        rejected = self.client.post("/tr/account/delete", data={
            "csrf_token": self.token(profile), "current_password": "WrongPass123",
            "confirmation": TEST_USERNAME,
        }, follow_redirects=True)
        self.assertIn("Mevcut şifren doğru değil", rejected.get_data(as_text=True))
        profile = self.client.get("/tr/profile").get_data(as_text=True)
        deleted = self.client.post("/tr/account/delete", data={
            "csrf_token": self.token(profile), "current_password": TEST_PASSWORD,
            "confirmation": TEST_USERNAME,
        }, follow_redirects=True)
        self.assertIn("kişisel verilerin kalıcı olarak silindi", deleted.get_data(as_text=True))
        with connect_database() as connection:
            row = connection.execute("SELECT username,email,is_active FROM user_accounts WHERE id=?", (self.deleted_user_id,)).fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row["is_active"], 0)
        self.assertTrue(row["email"].endswith("@invalid.local"))


if __name__ == "__main__":
    unittest.main()
