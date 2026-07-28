"""Idempotent v0.9.5 quality metadata migration.

This script deliberately does not mark listings as fully verified. It only records
internal audit status and fixes deterministic pricing_type mismatches.
"""
from __future__ import annotations
import json, sqlite3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
TOOLS=ROOT/'data/tools.json'; DB=ROOT/'database/atlasfind.db'
PILOT={'chatgpt','visual-studio-code','blender','davinci-resolve','audacity','libreoffice','mozilla-firefox','bitwarden','dropbox','steam'}

def expected_pricing(value):
    value=str(value).strip().lower()
    return {'free':'free','freemium':'freemium','paid':'paid','subscription':'paid','one-time purchase':'paid'}.get(value)

def run():
    tools=json.loads(TOOLS.read_text(encoding='utf-8'))
    for tool in tools:
        source=str(tool.get('rating_source','')).lower(); freshness=str(tool.get('freshness',{}).get('status','')).lower()
        if tool['slug'] in PILOT: status='partially_verified'
        elif 'catalog' in source or freshness in {'review-due','outdated'}: status='review_due'
        elif 'editorial' in source: status='partially_verified'
        else: status='unverified'
        tool['quality_status']=status
        tool['quality_review']={'scope':'internal-consistency-pilot' if tool['slug'] in PILOT else 'dataset-audit','reviewed_at':'2026-07-28','note':'Core fields were checked for internal consistency. Live pricing, platform support and feature availability still require confirmation on the official website.' if tool['slug'] in PILOT else 'This listing was included in the automated data-quality audit and still requires an individual editorial review.'}
        expected=expected_pricing(tool.get('pricing'))
        if expected: tool['pricing_type']=expected
    TOOLS.write_text(json.dumps(tools,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    con=sqlite3.connect(DB)
    for tool in tools: con.execute('UPDATE tools SET payload_json=?, updated_at=CURRENT_TIMESTAMP WHERE slug=?',(json.dumps(tool,ensure_ascii=False,separators=(',',':')),tool['slug']))
    con.commit(); con.close()
    print(f'Applied v0.9.5 quality metadata to {len(tools)} tools. No tool was marked fully verified.')
if __name__=='__main__': run()
