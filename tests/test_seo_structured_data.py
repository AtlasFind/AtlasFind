import unittest

from app import app, load_tools
from seo import software_schema


class SeoStructuredDataTests(unittest.TestCase):
    def test_catalog_score_is_not_published_as_user_review(self):
        tool = next(item for item in load_tools() if item["slug"] == "gemini")
        with app.test_request_context("/en/tools/gemini"):
            schema = software_schema(tool)

        self.assertNotIn("aggregateRating", schema)
        self.assertNotIn("review", schema)
        self.assertEqual(schema["additionalProperty"]["name"], "AtlasFind catalog score")
        self.assertEqual(schema["additionalProperty"]["maxValue"], 10)
        self.assertGreaterEqual(schema["additionalProperty"]["value"], 0)
        self.assertLessEqual(schema["additionalProperty"]["value"], 10)

    def test_all_tool_schemas_avoid_fake_review_markup(self):
        with app.test_request_context("/en/"):
            schemas = [software_schema(tool) for tool in load_tools()]

        self.assertTrue(schemas)
        self.assertTrue(all("aggregateRating" not in schema for schema in schemas))
        self.assertTrue(all("review" not in schema for schema in schemas))


if __name__ == "__main__":
    unittest.main()
