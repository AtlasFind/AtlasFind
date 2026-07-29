from __future__ import annotations
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from database import connect_database, DATABASE_PATH


def main() -> int:
    tools=json.loads((ROOT/'data/tools.json').read_text(encoding='utf-8'))
    by_slug={tool['slug']:tool.get('branding') for tool in tools if tool.get('slug')}
    updated=0
    with connect_database(DATABASE_PATH) as connection:
        rows=connection.execute('SELECT id, slug, payload_json FROM tools').fetchall()
        for row in rows:
            branding=by_slug.get(row['slug'])
            if branding is None:
                continue
            payload=json.loads(row['payload_json'])
            if payload.get('branding')==branding:
                continue
            payload['branding']=branding
            connection.execute('UPDATE tools SET payload_json=?, updated_at=CURRENT_TIMESTAMP WHERE id=?',(json.dumps(payload,ensure_ascii=False,separators=(',',':')),row['id']))
            updated+=1
        connection.commit()
    print(f'SQLite branding payloads synchronized: {updated}')
    return 0
if __name__=='__main__': raise SystemExit(main())
