"""Validate freshness metadata and the reusable update checklist."""
from __future__ import annotations
import json, sys
from pathlib import Path
BASE_DIR=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(BASE_DIR))
from tool_schema import validate_tools
from content_schema import validate_articles

def main()->int:
    tools=json.loads((BASE_DIR/'data'/'tools.json').read_text(encoding='utf-8'))
    articles=json.loads((BASE_DIR/'data'/'articles.json').read_text(encoding='utf-8'))
    checklist=json.loads((BASE_DIR/'data'/'update_checklist.json').read_text(encoding='utf-8'))
    errors=validate_tools(tools)+validate_articles(articles,{t.get('slug') for t in tools})
    items=checklist.get('items') if isinstance(checklist,dict) else None
    if not isinstance(items,list) or not items:
        errors.append('Update checklist must contain a non-empty items list.')
    else:
        seen=set()
        for index,item in enumerate(items):
            if not isinstance(item,dict): errors.append(f'Checklist item #{index+1} must be an object.'); continue
            item_id=item.get('id')
            if not isinstance(item_id,str) or not item_id.strip(): errors.append(f'Checklist item #{index+1} has an invalid id.')
            elif item_id in seen: errors.append(f'Duplicate checklist id: {item_id}.')
            else: seen.add(item_id)
            if not isinstance(item.get('label'),str) or not item['label'].strip(): errors.append(f'Checklist item #{index+1} has an invalid label.')
            if not isinstance(item.get('required'),bool): errors.append(f'Checklist item #{index+1} required must be boolean.')
    if errors:
        print('Freshness validation failed:')
        for error in errors: print(f'- {error}')
        return 1
    print(f'Validation successful: {len(tools)} tools, {len(articles)} articles and {len(items)} checklist items satisfy the v0.6.0 freshness schema.')
    return 0
if __name__=='__main__': raise SystemExit(main())
