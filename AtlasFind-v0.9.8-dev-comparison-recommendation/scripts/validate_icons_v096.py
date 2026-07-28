from __future__ import annotations
import json,sqlite3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
tools=json.loads((ROOT/'data'/'tools.json').read_text(encoding='utf-8'))
assert len(tools)==600
assert len({t['slug'] for t in tools})==600
for t in tools:
    assert t.get('icon_url'), t['slug']
    fallback=t.get('icon_fallback_url','')
    assert fallback.startswith('/static/icons/generated/'), (t['slug'],fallback)
    assert (ROOT/fallback.lstrip('/')).exists(), t['slug']
    assert t.get('icon_meta',{}).get('fallback')=='local-svg-monogram'
with sqlite3.connect(ROOT/'database'/'atlasfind.db') as con:
    payloads=[json.loads(r[0]) for r in con.execute('SELECT payload_json FROM tools ORDER BY id')]
assert len(payloads)==600
assert {t['slug']:t['icon_fallback_url'] for t in tools}=={t['slug']:t['icon_fallback_url'] for t in payloads}
js=(ROOT/'static/js/main.js').read_text(encoding='utf-8')
assert 'data-atlas-icon' in ''.join(p.read_text(encoding='utf-8') for p in (ROOT/'templates').glob('*.html'))
assert 'naturalWidth' in js and 'fallbackSrc' in js
print('v0.9.6 icon validation successful: 600 local fallbacks and SQLite parity confirmed.')
