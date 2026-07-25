# AtlasFind

**Find the right software. Faster.**

AtlasFind is a Flask-based software discovery, recommendation, comparison and editorial guide platform.

## Current Version

v0.4.1

## Current Features

- Typo-tolerant smart search with relevance explanations
- Multi-filter discovery with shareable URL state
- Professional tool pages and two-to-four tool comparison
- Local recommendation engine with transparent match reasons
- Category and collection discovery pages
- Data-driven software guides, alternatives and roundups
- Freshness badges, review schedules and change history
- Article table of contents, FAQs, related tools and internal links
- Dark/light themes and responsive navigation
- JSON datasets with validation scripts

## Run Locally

```bash
pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5000`.

## Validation

```powershell
python scripts/validate_tools.py
python scripts/validate_content.py
python scripts/validate_freshness.py
python scripts/test_search.py
python scripts/test_recommendations.py
```

## Adding a tool

Every entry in `data/tools.json` must satisfy the full scalable tool schema. The validation and application logic are not tied to a fixed tool count.

## Adding an article

Add a new entry to `data/articles.json` with:

- unique `slug`
- `title`, `description`, `content_type` and `category`
- ISO dates in `published_at` and `updated_at`
- reusable `sections`
- optional FAQs
- valid related tool and article slugs

Run `python scripts/validate_content.py
python scripts/validate_freshness.py` before committing. All articles use the shared `/guides/<slug>` template.
