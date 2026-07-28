from __future__ import annotations
import json, sqlite3, sys
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from taxonomy import CATEGORIES, category_slug

tools=json.loads((ROOT/'data'/'tools.json').read_text(encoding='utf-8'))
assert len(tools)==600
unknown=[t['category'] for t in tools if category_slug(t['category']) not in CATEGORIES]
assert not unknown, unknown[:5]
counts=Counter(category_slug(t['category']) for t in tools)
assert len(counts)==18, counts
assert all(counts[s]>0 for s in CATEGORIES)
con=sqlite3.connect(ROOT/'database'/'atlasfind.db')
try:
    assert con.execute('SELECT COUNT(*) FROM tools').fetchone()[0]==600
    assert con.execute('SELECT COUNT(*) FROM categories').fetchone()[0]==18
    missing=con.execute('SELECT COUNT(*) FROM tools WHERE category_id IS NULL').fetchone()[0]
    assert missing==0
finally: con.close()

# Turkish translation payloads must resolve to the same 18 canonical slugs.
con=sqlite3.connect(ROOT/'database'/'atlasfind.db')
con.row_factory=sqlite3.Row
try:
    translated_counts=Counter()
    unknown_translated=[]
    for row in con.execute("SELECT payload_json FROM tool_translations WHERE locale='tr'"):
        payload=json.loads(row['payload_json'] or '{}')
        raw_category=payload.get('category','')
        resolved=category_slug(raw_category)
        translated_counts[resolved]+=1
        if resolved not in CATEGORIES:
            unknown_translated.append(raw_category)
    assert sum(translated_counts.values())==600, translated_counts
    assert len(translated_counts)==18, translated_counts
    assert not unknown_translated, unknown_translated[:5]
    assert all(translated_counts[s]>0 for s in CATEGORIES), translated_counts
finally:
    con.close()

app=(ROOT/'app.py').read_text(encoding='utf-8')
base=(ROOT/'templates'/'base.html').read_text(encoding='utf-8')
assert 'def categories_directory' in app
assert 'def subcategory_page' in app
assert "url_for('categories_directory')" in base
assert 'APP_VERSION = "1.0.0"' in app
print('v0.9.4 taxonomy validation successful: 600 tools, 18 categories and Turkish/English category parity present.')
