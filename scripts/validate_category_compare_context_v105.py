from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
tools = json.loads((ROOT / "data" / "tools.json").read_text(encoding="utf-8"))
app = (ROOT / "app.py").read_text(encoding="utf-8")
index = (ROOT / "templates" / "index.html").read_text(encoding="utf-8")
categories = (ROOT / "templates" / "categories.html").read_text(encoding="utf-8")
discovery = (ROOT / "templates" / "discovery.html").read_text(encoding="utf-8")
compare = (ROOT / "templates" / "compare.html").read_text(encoding="utf-8")
javascript = (ROOT / "static" / "js" / "main.js").read_text(encoding="utf-8")

assert len(tools) == 600
assert len({tool["category"] for tool in tools}) == 18
assert len({tool.get("subcategory") for tool in tools if tool.get("subcategory")}) >= 100
assert "<strong>40+</strong>" not in index
assert "{{ category_count }}" in index
assert "category_total" in categories and "subcategory_total" in categories
assert "subcategory-detail-grid" in discovery and "category_landing.subcategory_cards" in discovery
assert "comparison_category_slug" in app and "category_mismatch_removed" in app
assert 'data-category="{{ category_slug(item.category) }}"' in compare
assert "primaryCategory" in javascript and "outsideCategory" in javascript

chatgpt = next(tool for tool in tools if tool["slug"] == "chatgpt")
seven_zip = next(tool for tool in tools if tool["slug"] == "7-zip")
assert chatgpt["category"] != seven_zip["category"]

print("Category detail and contextual comparison validation successful.")
print("- Tools: 600")
print("- Main categories: 18")
print(f"- Unique subcategories: {len({tool.get('subcategory') for tool in tools if tool.get('subcategory')})}")
