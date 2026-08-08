import unittest

from app import ADSENSE_PUBLISHER_ID, app


class AdSenseSetupTests(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True)
        self.client = app.test_client()

    def test_adsense_verification_meta_tag_is_present(self):
        response = self.client.get("/tr/")
        page = response.get_data(as_text=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            f'<meta name="google-adsense-account" content="{ADSENSE_PUBLISHER_ID}">',
            page,
        )
        self.assertNotIn("pagead2.googlesyndication.com/pagead/js/adsbygoogle.js", page)

    def test_ads_txt_declares_google_as_direct_seller(self):
        response = self.client.get("/ads.txt")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.get_data(as_text=True),
            "google.com, pub-7183165697400406, DIRECT, f08c47fec0942fa0\n",
        )

    def test_verification_does_not_weaken_content_security_policy(self):
        response = self.client.get("/tr/")
        policy = response.headers["Content-Security-Policy"]
        self.assertNotIn("'unsafe-eval'", policy)
        self.assertNotIn("'strict-dynamic'", policy)
        self.assertIn("connect-src 'self'", policy)


if __name__ == "__main__":
    unittest.main()
