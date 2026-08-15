import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))
from database import apply_migrations, connect_database
from i18n import DEFAULT_LOCALE, SUPPORTED_LOCALES, TRANSLATIONS_DIR

errors=[]
translations={}
for locale in SUPPORTED_LOCALES:
    path=TRANSLATIONS_DIR/f'{locale}.json'
    if not path.exists():
        errors.append(f'Missing translation file: {path.name}')
        continue
    translations[locale]=json.loads(path.read_text(encoding='utf-8'))
base_keys=set(translations.get(DEFAULT_LOCALE,{}))
for locale,data in translations.items():
    missing=sorted(base_keys-set(data))
    empty=sorted(key for key,value in data.items() if not str(value).strip())
    if missing: errors.append(f'{locale}: missing keys: {", ".join(missing)}')
    if empty: errors.append(f'{locale}: empty keys: {", ".join(empty)}')
apply_migrations()
with connect_database() as con:
    bad=con.execute("SELECT locale,COUNT(*) c FROM tool_translations WHERE locale NOT IN ('en','tr') GROUP BY locale").fetchall()
    if bad: errors.append('Invalid locales in tool_translations')
    duplicates=con.execute('SELECT tool_id,locale,COUNT(*) c FROM tool_translations GROUP BY tool_id,locale HAVING c>1').fetchall()
    if duplicates: errors.append('Duplicate tool translations detected')
if errors:
    print('Translation validation failed:')
    for error in errors: print('-',error)
    raise SystemExit(1)
print(f'Validation successful: {len(SUPPORTED_LOCALES)} locales and {len(base_keys)} interface keys satisfy the v0.6.1 translation schema.')


def validate_complete_turkish_content():
    with connect_database() as con:
        total = con.execute("SELECT COUNT(*) FROM tools WHERE COALESCE(status,'published')='published'").fetchone()[0]
        tr = con.execute("SELECT COUNT(*) FROM tool_translations WHERE locale='tr' AND TRIM(COALESCE(description,''))<>''").fetchone()[0]
    if tr != total:
        raise SystemExit(f"Turkish content incomplete: {tr}/{total} tools translated")
    print(f"Complete Turkish tool content: {tr}/{total}")

validate_complete_turkish_content()
