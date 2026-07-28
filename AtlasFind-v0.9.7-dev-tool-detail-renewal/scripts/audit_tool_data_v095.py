from __future__ import annotations
import json
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

ROOT=Path(__file__).resolve().parents[1]
TOOLS_PATH=ROOT/'data/tools.json'
REPORT_JSON=ROOT/'reports/data-quality-v095.json'
REPORT_MD=ROOT/'reports/data-quality-v095.md'
FIELDS=('pros','cons','target_users','system_requirements')

def signature(value):
    return json.dumps(value,ensure_ascii=False,sort_keys=True)

def run():
    tools=json.loads(TOOLS_PATH.read_text(encoding='utf-8'))
    duplicates={}
    for field in FIELDS:
        counts=Counter(signature(t.get(field,[])) for t in tools)
        duplicates[field]=[{'count':count,'value':json.loads(sig)} for sig,count in counts.most_common() if count>1]
    bad_urls=[]; missing_languages=[]; pricing_mismatches=[]
    for t in tools:
        parsed=urlparse(str(t.get('website','')))
        if parsed.scheme not in {'http','https'} or not parsed.netloc: bad_urls.append(t['slug'])
        if not t.get('languages'): missing_languages.append(t['slug'])
        p=str(t.get('pricing','')).lower(); expected='free' if p=='free' else 'freemium' if p=='freemium' else 'paid' if p in {'paid','subscription','one-time purchase'} else None
        if expected and t.get('pricing_type')!=expected: pricing_mismatches.append({'slug':t['slug'],'pricing':t.get('pricing'),'pricing_type':t.get('pricing_type')})
    status=Counter(t.get('quality_status','missing') for t in tools)
    report={'tool_count':len(tools),'quality_status_counts':dict(status),'bad_urls':bad_urls,'missing_languages':missing_languages,'pricing_mismatches':pricing_mismatches,'repeated_content':duplicates}
    REPORT_JSON.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    lines=['# AtlasFind v0.9.5 Data Quality Audit','',f'- Tools audited: **{len(tools)}**',f'- Invalid URL formats: **{len(bad_urls)}**',f'- Missing language metadata: **{len(missing_languages)}**',f'- Pricing mismatches: **{len(pricing_mismatches)}**','', '## Verification status']
    lines += [f'- {k}: **{v}**' for k,v in sorted(status.items())]
    lines += ['', '## Repeated editorial fields']
    for field in FIELDS:
        top=duplicates[field][:3]
        lines.append(f'### {field}')
        lines.extend(f'- Repeated {x["count"]} times: {" | ".join(x["value"])}' for x in top)
        lines.append('')
    lines += ['## Interpretation','','The audit detects internal consistency and repetition. It does not prove that live pricing, feature availability or platform support is current. Those fields require an individual editorial check against the official website.','']
    REPORT_MD.write_text('\n'.join(lines),encoding='utf-8')
    print(f'Audit complete: {len(tools)} tools, {len(missing_languages)} missing language metadata, {len(pricing_mismatches)} pricing mismatches.')
if __name__=='__main__': run()
