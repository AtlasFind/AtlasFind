from pathlib import Path
import os
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

checks = {
    "security.py": ROOT / "security.py",
    ".env.example": ROOT / ".env.example",
    "error template": ROOT / "templates" / "error.html",
}
missing = [name for name, path in checks.items() if not path.exists()]
if missing:
    raise SystemExit("Missing security files: " + ", ".join(missing))

app_text = (ROOT / "app.py").read_text(encoding="utf-8")
auth_text = (ROOT / "admin" / "auth.py").read_text(encoding="utf-8")
routes_text = (ROOT / "admin" / "routes.py").read_text(encoding="utf-8")
required_app = ["configure_security(app)", "configure_logging(app)", "add_security_headers", "ATLASFIND_DEBUG"]
required_auth = ["last_admin_activity", "SESSION_IDLE_SECONDS"]
required_routes = ["enforce_admin_login_rate_limit", "client_ip()"]
errors = []
for token in required_app:
    if token not in app_text: errors.append(f"app.py missing {token}")
for token in required_auth:
    if token not in auth_text: errors.append(f"admin/auth.py missing {token}")
for token in required_routes:
    if token not in routes_text: errors.append(f"admin/routes.py missing {token}")
if errors:
    raise SystemExit("Security validation failed:\n- " + "\n- ".join(errors))
print("Security validation successful: production config, admin timeout, rate limiting, headers, logging and safe errors are present.")
