from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
required=["templates/public_page.html","translations/en.json","translations/tr.json","static/js/main.js","static/css/style.css"]
missing=[x for x in required if not (ROOT/x).exists()]
if missing: raise SystemExit("Missing: "+", ".join(missing))
en=json.loads((ROOT/"translations/en.json").read_text(encoding="utf-8")); tr=json.loads((ROOT/"translations/tr.json").read_text(encoding="utf-8"))
keys={"footer.privacy","footer.terms","footer.cookies","footer.contact","cookie.message","cookie.accept"}
for locale,data in (("en",en),("tr",tr)):
    absent=sorted(keys-data.keys())
    if absent: raise SystemExit(f"{locale} missing keys: {absent}")
app=(ROOT/"app.py").read_text(encoding="utf-8")
for route in ("privacy","terms","cookies","contact"):
    if f'def {route}(' not in app: raise SystemExit(f"Missing route: {route}")
print("Public beta validation successful: legal pages, contact routes, cookie notice and bilingual footer are present.")
