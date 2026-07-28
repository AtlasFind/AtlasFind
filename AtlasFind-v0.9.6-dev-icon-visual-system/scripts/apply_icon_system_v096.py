from __future__ import annotations
import json, sqlite3
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from icon_system import ensure_local_icon, icon_initials, website_domain

DATA=ROOT/'data'/'tools.json'
DB=ROOT/'database'/'atlasfind.db'

tools=json.loads(DATA.read_text(encoding='utf-8'))
for tool in tools:
    local=ensure_local_icon(tool['name'],tool['slug'])
    tool['icon_fallback_url']=local
    tool['icon_source']='simple-icons-with-local-monogram-fallback'
    tool['icon_alt']=tool.get('icon_alt') or f"{tool['name']} icon"
    tool['icon_meta']={
        'fallback':'local-svg-monogram',
        'initials':icon_initials(tool['name']),
        'domain':website_domain(tool.get('website','')),
        'lazy_load':True,
        'review_status':'automated',
    }
DATA.write_text(json.dumps(tools,ensure_ascii=False,indent=2)+"\n",encoding='utf-8')

with sqlite3.connect(DB) as con:
    for tool in tools:
        con.execute('UPDATE tools SET payload_json=? WHERE slug=?',(json.dumps(tool,ensure_ascii=False),tool['slug']))
    con.commit()
print(f'Applied local icon fallback metadata to {len(tools)} tools.')
