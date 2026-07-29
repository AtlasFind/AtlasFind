from pathlib import Path
import json, sys
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from catalog.loader import load_catalog
from database import apply_migrations, transaction

def main():
    apply_migrations()
    tools=load_catalog(validate=True)
    updated=0
    with transaction() as connection:
        for tool in tools:
            row=connection.execute("SELECT id FROM tools WHERE slug=?",(tool.get('slug'),)).fetchone()
            if not row: continue
            connection.execute("UPDATE tools SET rating=?, payload_json=?, updated_at=CURRENT_TIMESTAMP WHERE slug=?",(tool.get('rating',0),json.dumps(tool,ensure_ascii=False),tool.get('slug')))
            updated+=1
    print(f"SQLite rating payloads synchronized: {updated}")
if __name__=='__main__': main()
