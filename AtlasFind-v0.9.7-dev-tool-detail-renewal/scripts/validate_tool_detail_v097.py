from pathlib import Path
import json,re
ROOT=Path(__file__).resolve().parents[1]
app=(ROOT/'app.py').read_text(encoding='utf-8')
tpl=(ROOT/'templates/tool.html').read_text(encoding='utf-8')
css=(ROOT/'static/css/style.css').read_text(encoding='utf-8')
assert 'APP_VERSION = "0.9.7-dev"' in app
for token in ['tool-detail-jump','compare_tool','pricing-card','quality-badge','alternatives_to']:
    assert token in tpl or token in css, token
assert 'Visit official website' not in tpl
assert 'Quick summary' not in tpl
assert 'No alternatives found yet' not in tpl
for lang in ('tr','en'):
    data=json.loads((ROOT/'translations'/f'{lang}.json').read_text(encoding='utf-8'))
    for key in ['tool.seo_title','tool.visit_official','tool.quick_summary','tool.alternatives_to','common.unknown']:
        assert key in data, (lang,key)
assert "url_for(\'tool_detail\', locale=locale" in tpl
assert "url_for(\'compare_tools\', locale=locale" in tpl
print('v0.9.7 tool detail validation successful.')
