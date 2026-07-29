from __future__ import annotations
import argparse, json, sys
from datetime import datetime, timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from catalog.loader import load_catalog


def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument('--output', default='data/branding/logo-queue.json')
    args=parser.parse_args()
    tools=load_catalog()
    queue=[]
    for tool in tools:
        branding=tool.get('branding') or {}
        logo=branding.get('logo') or {}
        if logo.get('status') == 'verified':
            continue
        official=(tool.get('official_links') or {}).get('website') or tool.get('website')
        queue.append({
            'tool_id': tool.get('id'), 'slug': tool.get('slug'), 'name': tool.get('name'),
            'official_url': official, 'status': 'pending', 'attempts': 0,
            'candidates': [], 'last_error': None, 'updated_at': None,
        })
    path=ROOT/args.output; path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps({'version':1,'generated_at':datetime.now(timezone.utc).isoformat(),'total':len(queue),'items':queue},ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'Logo discovery queue created: {len(queue)} tools -> {path.relative_to(ROOT)}')
    return 0
if __name__=='__main__': raise SystemExit(main())
