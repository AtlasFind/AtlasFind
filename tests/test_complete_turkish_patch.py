import re
import unittest

from app import app, load_articles, load_tools


ENGLISH_GLUE = re.compile(
    r"\b(?:and|assistant|tasks|management|tools|applications|documents|knowledge|storage|sync|"
    r"security|utilities|writing|editing|search engines|file sharing|team chat|personal finance)\b",
    re.I,
)


class CompleteTurkishPatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tools = load_tools("tr")

    def test_every_tool_has_complete_turkish_visible_fields(self):
        self.assertEqual(1000, len(self.tools))
        scalar_fields = ("description", "purpose", "category", "subcategory", "pricing", "icon_alt")
        list_fields = ("features", "tags", "pros", "cons", "target_users", "system_requirements")
        for tool in self.tools:
            for field in scalar_fields:
                value = str(tool.get(field) or "").strip()
                self.assertTrue(value, f"{tool['slug']}.{field}")
                inspected = value.removeprefix(tool["name"]).strip(" ,;:-")
                self.assertIsNone(ENGLISH_GLUE.search(inspected), f"{tool['slug']}.{field}: {value}")
            for field in list_fields:
                values = tool.get(field) or []
                self.assertTrue(values, f"{tool['slug']}.{field}")
                for value in values:
                    self.assertIsNone(ENGLISH_GLUE.search(str(value)), f"{tool['slug']}.{field}: {value}")
            self.assertTrue((tool.get("pricing_details") or {}).get("note"), tool["slug"])
            self.assertTrue((tool.get("verification") or {}).get("note"), tool["slug"])
            self.assertTrue((tool.get("quality_review") or {}).get("note"), tool["slug"])

    def test_main_turkish_pages_render_without_translation_keys(self):
        with app.test_client() as client:
            for path in ("/tr/", "/tr/tools", "/tr/categories", "/tr/compare", "/tr/about", "/tr/tools/chatgpt", "/tr/tools/beelzebub"):
                response = client.get(path)
                self.assertEqual(200, response.status_code, path)
                text = response.get_data(as_text=True)
                self.assertNotRegex(text, r">(?:nav|tool|catalog|common|actions|quality)\.[a-z0-9_.-]+<", path)

    def test_all_guides_have_complete_turkish_payloads(self):
        articles = load_articles("tr")
        self.assertEqual(6, len(articles))
        for article in articles:
            self.assertIsInstance(article.get("id"), int, article["slug"])
            self.assertTrue(article.get("title"), article["slug"])
            self.assertTrue(article.get("description"), article["slug"])
            self.assertTrue(article.get("sections"), article["slug"])
            self.assertTrue(article.get("faq"), article["slug"])
            self.assertEqual("AtlasFind Editörleri", article.get("author"), article["slug"])
            for section in article["sections"]:
                self.assertTrue(section.get("title"), article["slug"])
                self.assertTrue(section.get("paragraphs"), article["slug"])


if __name__ == "__main__":
    unittest.main()
