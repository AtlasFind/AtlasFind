"""Bootstrap persistent data, then replace this process with Gunicorn."""
from pathlib import Path
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    subprocess.run([sys.executable, str(ROOT / "scripts" / "bootstrap_database.py")], check=True)
    port = os.environ.get("PORT", "8000")
    workers = os.environ.get("WEB_CONCURRENCY", "2")
    timeout = os.environ.get("GUNICORN_TIMEOUT", "60")
    command = [
        "gunicorn",
        "--bind", f"0.0.0.0:{port}",
        "--workers", workers,
        "--threads", "2",
        "--timeout", timeout,
        "--access-logfile", "-",
        "--error-logfile", "-",
        "wsgi:app",
    ]
    os.chdir(ROOT)
    os.execvp(command[0], command)


if __name__ == "__main__":
    main()
