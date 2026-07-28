from pathlib import Path
import json, re, sys
ROOT=Path(__file__).resolve().parents[1]
en=json.loads((ROOT/"translations/en.json").read_text(encoding="utf-8"))
tr=json.loads((ROOT/"translations/tr.json").read_text(encoding="utf-8"))
errors=[]
if set(en)!=set(tr):
    errors.append(f"Translation key mismatch: EN-only={sorted(set(en)-set(tr))[:10]} TR-only={sorted(set(tr)-set(en))[:10]}")
for locale,data in (("en",en),("tr",tr)):
    for key,value in data.items():
        if key != "quality" and (not isinstance(value,str) or not value.strip()): errors.append(f"Empty translation: {locale}:{key}")
js=(ROOT/"static/js/main.js").read_text(encoding="utf-8")
# Ensure required integration points exist
for needle,path in [("window.ATLAS_I18N",ROOT/"templates/base.html"),("atlasT(\"js.menu.open",ROOT/"static/js/main.js"),("APP_VERSION = \"1.0.1\"",ROOT/"app.py")]:
    if needle not in path.read_text(encoding="utf-8"): errors.append(f"Missing integration: {needle}")
if errors:
    print("Localization validation failed:")
    print("\n".join(f"- {e}" for e in errors)); sys.exit(1)
print(f"Localization validation successful: {len(en)} synchronized keys, EN/TR switcher and JS catalog present.")
