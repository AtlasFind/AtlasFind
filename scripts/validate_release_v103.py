from pathlib import Path
import subprocess,sys
ROOT=Path(__file__).resolve().parents[1]
commands=[
 [sys.executable,'scripts/validate_ratings_v103.py'],
 [sys.executable,'scripts/validate_catalog_v102.py'],
 [sys.executable,'scripts/validate_translations.py'],
 [sys.executable,'-m','unittest','discover','-s','tests','-p','test_rating*.py'],
]
for command in commands:
 print('>', ' '.join(command)); subprocess.run(command,cwd=ROOT,check=True)
print('AtlasFind v1.0.3 release validation successful.')
