from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
errors = []
required = [
    "wsgi.py", "Dockerfile", ".dockerignore", "render.yaml",
    "scripts/bootstrap_database.py", "scripts/start_production.py",
    "docs/DEPLOYMENT.md",
]
for item in required:
    if not (ROOT / item).exists():
        errors.append(f"Missing deployment file: {item}")

app_text = (ROOT / "app.py").read_text(encoding="utf-8")
for route in ('@app.route("/health")', '@app.route("/ready")'):
    if route not in app_text:
        errors.append(f"Missing route: {route}")

reqs = (ROOT / "requirements.txt").read_text(encoding="utf-8").lower()
if "gunicorn" not in reqs:
    errors.append("gunicorn is missing from requirements.txt")

db_text = (ROOT / "database.py").read_text(encoding="utf-8")
if "ATLASFIND_DATABASE_PATH" not in db_text:
    errors.append("Database path is not configurable for persistent storage")

if errors:
    print("Deployment validation failed:")
    for error in errors:
        print(f"- {error}")
    raise SystemExit(1)
print("Deployment validation successful: WSGI, health checks, persistent database path, bootstrap and container files are present.")
