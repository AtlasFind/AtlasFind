import json
import unittest

from catalog.loader import load_published_catalog
from scripts.sync_complete_turkish_translations import (
    LEGACY_DESCRIPTION_MARKERS,
    merge_missing,
    payload_for,
    should_replace_translation,
)


class _Row(dict):
    pass


class TurkishTranslationSyncTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tools = load_published_catalog(validate=True)

    def test_curated_translation_is_preserved(self):
        row = _Row(
            description="Editör tarafından hazırlanmış özgün bir Türkçe açıklama.",
            payload_json=json.dumps({"translation_source": "curated-v1"}),
        )
        self.assertFalse(should_replace_translation(row))

    def test_legacy_generated_translation_is_replaced(self):
        row = _Row(
            description="Örnek, alanındaki işleri düzenlemeye ve yürütmeye yardımcı olan bir araçtır.",
            payload_json="{}",
        )
        self.assertTrue(should_replace_translation(row))

    def test_editorial_payload_wins_while_missing_fields_are_filled(self):
        defaults = {"description": "Fallback", "purpose": "Fallback", "pricing_details": {"model": "Ücretsiz", "note": "Not"}}
        existing = {"description": "Özgün", "pricing_details": {"model": "Kurumsal"}}
        merged = merge_missing(defaults, existing)
        self.assertEqual(merged["description"], "Özgün")
        self.assertEqual(merged["purpose"], "Fallback")
        self.assertEqual(merged["pricing_details"], {"model": "Kurumsal", "note": "Not"})

    def test_every_tool_gets_non_legacy_description(self):
        descriptions = [payload_for(tool)["description"] for tool in self.tools]
        self.assertEqual(len(descriptions), 1000)
        self.assertTrue(all(description.strip() for description in descriptions))
        for description in descriptions:
            self.assertFalse(any(marker in description.lower() for marker in LEGACY_DESCRIPTION_MARKERS))

    def test_priority_tools_have_curated_copy(self):
        by_slug = {tool["slug"]: tool for tool in self.tools}
        chatgpt = payload_for(by_slug["chatgpt"])["description"]
        claude = payload_for(by_slug["claude"])["description"]
        self.assertIn("dosya analizi", chatgpt)
        self.assertIn("uzun belgeler", claude)
        self.assertNotEqual(chatgpt, claude)


if __name__ == "__main__":
    unittest.main()
