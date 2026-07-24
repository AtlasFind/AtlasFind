# AtlasFind

**Find the right software. Faster.**

AtlasFind is a software discovery and comparison platform built with Flask.

## Current Version

v0.1.2

## Current Features

- Software search
- Premium responsive interface
- Tool cards and detail pages
- Side-by-side comparison
- Dark and light themes
- Mobile navigation
- Empty and loading states
- JSON-based tool dataset with schema validation
- Accessibility improvements

## Technology

- Python
- Flask
- HTML and Jinja
- CSS
- JavaScript
- JSON

## Run Locally

```bash
pip install -r requirements.txt
python app.py
```

Then open `http://127.0.0.1:5000`.

## Development Status

v0.1.2 - Premium Appearance completed. Later versions require separate approval before development begins.

## Adding a new tool

Every current and future entry in `data/tools.json` must include the full professional detail-page schema. Required professional fields are:

- `pros`
- `cons`
- `target_users`
- `system_requirements`
- `pricing_details.model`
- `pricing_details.note`
- `verification.status`
- `verification.date`
- `verification.note`

The application validates the complete dataset whenever it loads. Before committing a new tool, run:

```powershell
python scripts/validate_tools.py
```

The command checks every entry dynamically. There is no hard-coded tool-count limit, so the same rules apply whether AtlasFind contains 100 tools or several thousand.
