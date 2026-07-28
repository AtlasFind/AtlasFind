from __future__ import annotations
import json,re
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
tools=json.loads((ROOT/'data'/'tools.json').read_text(encoding='utf-8'))
issues=[]
primary=Counter(); fallback=Counter()
for tool in tools:
    slug=tool.get('slug','')
    p=tool.get('icon_url',''); f=tool.get('icon_fallback_url','')
    primary[p.split('/')[2] if p.startswith('http') else 'local-or-missing']+=1
    fallback['local' if f.startswith('/static/icons/generated/') else 'external-or-missing']+=1
    expected=ROOT/f.lstrip('/') if f.startswith('/') else None
    if not p: issues.append({'slug':slug,'issue':'missing-primary'})
    if not f: issues.append({'slug':slug,'issue':'missing-fallback'})
    elif expected and not expected.exists(): issues.append({'slug':slug,'issue':'missing-local-file'})
    if '<' in tool.get('icon_alt','') or '>' in tool.get('icon_alt',''): issues.append({'slug':slug,'issue':'unsafe-alt'})
report={'total':len(tools),'primary_hosts':dict(primary),'fallback_types':dict(fallback),'issues':issues,'issue_count':len(issues)}
out=ROOT/'reports'; out.mkdir(exist_ok=True)
(out/'icon-audit-v096.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding='utf-8')
(out/'icon-audit-v096.md').write_text(f"# AtlasFind Icon Audit v0.9.6\n\n- Tools: {len(tools)}\n- Local fallbacks: {fallback['local']}\n- Issues: {len(issues)}\n- Primary hosts: {dict(primary)}\n",encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
