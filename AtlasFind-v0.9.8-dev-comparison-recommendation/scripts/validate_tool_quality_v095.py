from __future__ import annotations
import json, sqlite3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
tools=json.loads((ROOT/'data/tools.json').read_text(encoding='utf-8'))
assert len(tools)==600
allowed={'verified','partially_verified','unverified','review_due'}
assert all(t.get('quality_status') in allowed for t in tools)
assert all(set(t.get('quality_review',{})) >= {'scope','reviewed_at','note'} for t in tools)
assert not any(t.get('quality_status')=='verified' for t in tools), 'Automated migration must not claim full verification.'
con=sqlite3.connect(ROOT/'database/atlasfind.db')
rows=con.execute('SELECT slug,payload_json FROM tools ORDER BY id').fetchall(); con.close()
assert len(rows)==600
json_by_slug={t['slug']:t for t in tools}
for slug,payload in rows:
    db=json.loads(payload)
    assert db.get('quality_status')==json_by_slug[slug].get('quality_status')
for lang in ('tr','en'):
    d=json.loads((ROOT/f'translations/{lang}.json').read_text(encoding='utf-8'))
    for key in allowed|{'quality_status','quality_notice'}: assert d.get('quality',{}).get(key)
for path,needle in [('templates/discovery.html','quality-badge'),('templates/tool.html','quality-summary'),('static/css/style.css','.quality-badge')]:
    assert needle in (ROOT/path).read_text(encoding='utf-8')
print('v0.9.5 quality validation successful: 600 JSON/SQLite records, transparent status labels, no false full-verification claim.')
