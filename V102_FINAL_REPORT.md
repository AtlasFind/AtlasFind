# AtlasFind v1.0.2 Final Report

## Delivered

- Modular category-based catalog with 18 files and a manifest.
- Strict schema, taxonomy, duplicate, path and evidence validation.
- Compatibility build output for the existing application and SQLite migration path.
- Search index generation and 100/1,000/5,000/10,000 record benchmark tooling.
- Evidence audit, verification batches and publication-gate support.
- Five first-party verified reference records: Visual Studio Code, Blender, DaVinci Resolve, ChatGPT and Claude.
- Unverified ratings removed from the verified reference records.
- One-command Windows startup and consolidated release validation.

## Honest data state

- Total records: 600
- Strict verified records: 5
- Pending records: 595
- Published compatibility records: 600

The pending records remain available so the current site does not become empty. They are not represented as source-verified. Completing first-party verification for every pending record is an editorial research operation, not something that can be safely generated in bulk.

## Start

Run `run_atlasfind.bat`, or execute:

```powershell
py -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python scripts\validate_release_v102.py
.venv\Scripts\python app.py
```
