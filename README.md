# AtlasFind

**Find the right software. Faster.**

AtlasFind is a Flask-based software discovery and comparison platform.

## Current Version

v0.3.0

## Current Features

- Search with relevance scoring
- Multi-filter discovery using pricing, license, offline support, AI, platform, RAM, system level and Turkish support
- Shareable URL-based filter state
- Tool cards and professional detail pages
- Side-by-side comparison
- Dark/light themes and responsive navigation
- JSON dataset with dynamic schema validation
- Local recommendation engine with transparent match reasons

## Run Locally

```bash
pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5000`.

## Adding a new tool

Every entry in `data/tools.json` must satisfy the full schema. Filter-related fields are:

- `pricing_type`: `free`, `freemium` or `paid`
- `open_source`: boolean
- `offline`: boolean
- `ai_powered`: boolean
- `platforms`: one or more supported platform names
- `minimum_ram_gb`: positive number or `null` when unknown
- `system_level`: `light`, `medium`, `heavy` or `unknown`
- `languages`: ISO-like codes currently supported by the schema (`en`, `tr`)

Validate every current and future entry with:

```powershell
python scripts/validate_tools.py
```

The validation and filter logic are not tied to a fixed tool count.


## v0.2.0 Discovery
Browse category and collection pages with scalable sorting and pagination.


## v0.2.2 Smart Recommendations
Open `/recommend` to rank tools by purpose, platform, budget, hardware, experience, privacy and offline requirements. The engine is deterministic, transparent and independent of external AI APIs.


## v0.3.0 Smart Search
Typo-tolerant bilingual search, natural-query intent detection, suggestions, and filter-compatible weighted ranking.
