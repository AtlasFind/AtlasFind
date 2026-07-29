from __future__ import annotations
import json
import subprocess
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def run(*args):
    print('>', ' '.join(args))
    subprocess.run(args,cwd=ROOT,check=True)

def main():
    sys.path.insert(0,str(ROOT))
    app_source=(ROOT/'app.py').read_text(encoding='utf-8')
    if 'APP_VERSION = "1.0.4"' not in app_source:
        raise SystemExit('APP_VERSION is not 1.0.4')
    en=json.loads((ROOT/'translations/en.json').read_text(encoding='utf-8'))
    tr=json.loads((ROOT/'translations/tr.json').read_text(encoding='utf-8'))
    if set(en)!=set(tr): raise SystemExit('EN/TR translation keys do not match')
    run(sys.executable,'scripts/validate_tool_images_v104.py')
    run(sys.executable,'-m','unittest','tests.test_image_validation')
    run(sys.executable,'-m','compileall','-q','app.py','services','validators','admin','scripts')
    print(f'Translation keys: {len(en)}')
    print('AtlasFind v1.0.4 release validation successful.')
if __name__=='__main__': main()
