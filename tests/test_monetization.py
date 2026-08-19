import unittest
import sqlite3
from database import DATABASE_PATH
from datetime import date, timedelta

from app import active_featured_tools, app, safe_http_url, tool_outbound_url


class MonetizationTests(unittest.TestCase):
    def test_expired_and_legacy_tools_are_not_featured(self):
        future = (date.today() + timedelta(days=5)).isoformat()
        past = (date.today() - timedelta(days=1)).isoformat()
        tools = [
            {"slug": "legacy"},
            {"slug": "expired", "is_featured": True, "featured_until": past},
            {"slug": "active", "is_featured": True, "is_sponsored": True, "featured_until": future},
        ]
        self.assertEqual(["active"], [item["slug"] for item in active_featured_tools(tools)])
        self.assertEqual(["active"], [item["slug"] for item in active_featured_tools(tools, sponsored_only=True)])

    def test_affiliate_url_requires_http_or_https(self):
        self.assertIsNone(safe_http_url("javascript:alert(1)"))
        self.assertIsNone(safe_http_url("data:text/html,test"))
        self.assertEqual("https://partner.example/product", tool_outbound_url({"website": "https://example.com", "affiliate_url": "https://partner.example/product"}))
        self.assertEqual("https://example.com", tool_outbound_url({"website": "https://example.com", "affiliate_url": "javascript:alert(1)"}))

    def test_advertise_pages_and_sitemap(self):
        client = app.test_client()
        for path, heading in (("/en/advertise", "Promote Your Software"), ("/tr/advertise", "Yazılımınızı AtlasFind")):
            response = client.get(path)
            self.assertEqual(200, response.status_code)
            self.assertIn(heading, response.get_data(as_text=True))
        sitemap = client.get("/sitemap.xml").get_data(as_text=True)
        self.assertIn("/en/advertise", sitemap)
        self.assertIn("/tr/advertise", sitemap)

    def test_migration_columns_and_admin_template(self):
        with sqlite3.connect(DATABASE_PATH) as connection:
            columns = {row[1] for row in connection.execute("PRAGMA table_info(tools)")}
        self.assertTrue({"is_featured", "is_sponsored", "featured_until", "sponsor_plan", "affiliate_url"}.issubset(columns))
        template = app.jinja_env.get_template("admin/tool_form.html")
        self.assertIsNotNone(template)


if __name__ == "__main__":
    unittest.main()
