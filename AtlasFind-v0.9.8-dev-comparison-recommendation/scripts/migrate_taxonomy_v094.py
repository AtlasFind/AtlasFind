from __future__ import annotations
import json, sqlite3
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from taxonomy import CATEGORIES, category_slug

JSON_PATH=ROOT/'data'/'tools.json'
DB_PATH=ROOT/'database'/'atlasfind.db'

SUBCATEGORY_FIXES={
    'Database Tools':'Database Management',
    'Databases':'Database Management',
    'SQL Databases':'Databases',
    'Security Tools':'Security Utilities',
    'Development Tools':'Developer Utilities',
}

def migrate_tools(tools):
    changed=0
    for tool in tools:
        old=tool.get('category','')
        slug=category_slug(old)
        if slug not in CATEGORIES:
            raise ValueError(f'Unknown category: {old}')
        new=CATEGORIES[slug]['name_en']
        if old!=new:
            tool['category']=new; changed+=1
        sub=tool.get('subcategory')
        if sub in SUBCATEGORY_FIXES:
            tool['subcategory']=SUBCATEGORY_FIXES[sub]
    return changed

def main():
    tools=json.loads(JSON_PATH.read_text(encoding='utf-8'))
    sample=json.loads(json.dumps(tools[:10]))
    migrate_tools(sample)
    assert len(sample)==10 and all(category_slug(t['category']) in CATEGORIES for t in sample)
    changed=migrate_tools(tools)
    JSON_PATH.write_text(json.dumps(tools,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

    con=sqlite3.connect(DB_PATH)
    con.row_factory=sqlite3.Row
    try:
        con.execute('PRAGMA foreign_keys=OFF')
        con.execute('DELETE FROM categories')
        for slug,info in CATEGORIES.items():
            con.execute('INSERT INTO categories(slug,name) VALUES (?,?)',(slug,info['name_en']))
        ids={r['name']:r['id'] for r in con.execute('SELECT id,name FROM categories')}
        for tool in tools:
            payload=json.dumps(tool,ensure_ascii=False)
            con.execute('UPDATE tools SET category_id=?, subcategory=?, payload_json=?, updated_at=CURRENT_TIMESTAMP WHERE slug=?',
                        (ids[tool['category']],tool.get('subcategory'),payload,tool['slug']))
        con.commit()
    finally:
        con.close()
    print(f'Taxonomy migration successful: {len(tools)} tools, {changed} category changes, {len(CATEGORIES)} categories.')

if __name__=='__main__': main()
