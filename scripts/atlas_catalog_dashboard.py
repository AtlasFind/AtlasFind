"""Local editorial dashboard and optional process controller for the catalog worker."""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import subprocess
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.catalog_worker_record_service import build_review_records
from services.catalog_worker_export_service import create_export_package
from services.catalog_worker_review_service import export_readiness, load_reviews, merge_reviews, save_review

CATALOG = ROOT / "data/tools.json"
QUEUE = ROOT / "data/research/overnight-tool-candidates.json"
RECORDS = ROOT / "data/research/catalog-worker-records.json"
WORKER = ROOT / "scripts/catalog_worker_orchestrator.py"
STOP_FILE = ROOT / "data/research/catalog-worker.stop"
TEMPLATE = ROOT / "templates/catalog_worker_dashboard.html"
HOST, PORT = "127.0.0.1", 8765
PROCESS: subprocess.Popen | None = None


def start_worker() -> tuple[bool, str]:
    global PROCESS
    if PROCESS and PROCESS.poll() is None:
        return False, "already_running"
    STOP_FILE.unlink(missing_ok=True)
    PROCESS = subprocess.Popen([sys.executable, str(WORKER), "--cycle-minutes", "20"], cwd=ROOT)
    return True, "started"


def records_payload() -> dict:
    if RECORDS.exists():
        records = json.loads(RECORDS.read_text(encoding="utf-8"))
    else:
        catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
        queue = json.loads(QUEUE.read_text(encoding="utf-8")) if QUEUE.exists() else {"items": []}
        records = build_review_records(queue.get("items", []), catalog)
    return {
        "records": merge_reviews(records, load_reviews()),
        "running": bool(PROCESS and PROCESS.poll() is None),
        "auto_publish_allowed": False,
    }


class Handler(BaseHTTPRequestHandler):
    def send(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def json_body(self) -> dict:
        length = min(int(self.headers.get("Content-Length", "0")), 1_000_000)
        return json.loads(self.rfile.read(length).decode("utf-8"))

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/records":
            self.send(200, json.dumps(records_payload(), ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")
        elif path == "/":
            self.send(200, TEMPLATE.read_bytes(), "text/html; charset=utf-8")
        else:
            self.send(404, b"Not found", "text/plain")

    def do_POST(self) -> None:
        global PROCESS
        path = urlparse(self.path).path
        if path == "/api/start":
            started, status = start_worker()
            body = json.dumps({"ok": True, "started": started, "status": status}).encode("utf-8")
            return self.send(200, body, "application/json; charset=utf-8")
        if path == "/api/stop":
            if PROCESS and PROCESS.poll() is None:
                STOP_FILE.write_text("stop requested\n", encoding="utf-8")
                try:
                    PROCESS.wait(timeout=45)
                except subprocess.TimeoutExpired:
                    PROCESS.terminate()
                    try:
                        PROCESS.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        PROCESS.kill()
                        PROCESS.wait(timeout=5)
            try:
                exported = create_export_package(records_payload()["records"])
                body = json.dumps({"ok": True, "export": exported}, ensure_ascii=False).encode("utf-8")
                return self.send(200, body, "application/json; charset=utf-8")
            except (OSError, ValueError, sqlite3.Error) as exc:
                body = json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False).encode("utf-8")
                return self.send(500, body, "application/json; charset=utf-8")
        if path.startswith("/api/review/"):
            slug = unquote(path.removeprefix("/api/review/"))
            try:
                record = next((record for record in records_payload()["records"] if record["slug"] == slug), None)
                if record is None:
                    raise ValueError("Unknown record")
                payload = self.json_body()
                if payload.get("decision") == "approved_for_export":
                    blockers = export_readiness(record)
                    if blockers:
                        raise ValueError("Export approval blocked: " + "; ".join(blockers))
                result = save_review(slug, payload)
                return self.send(200, json.dumps(result, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")
            except (ValueError, json.JSONDecodeError) as exc:
                return self.send(400, json.dumps({"error": str(exc)}, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")
        self.send(404, b"Not found", "text/plain")

    def log_message(self, *_: object) -> None:
        pass


def main() -> None:
    global PROCESS
    parser = argparse.ArgumentParser()
    parser.add_argument("--start-worker", action="store_true", help="Explicitly start unlimited discovery")
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()
    if args.start_worker:
        try:
            request = Request(f"http://{HOST}:{PORT}/api/start", data=b"{}", method="POST",
                              headers={"Content-Type": "application/json"})
            with urlopen(request, timeout=3):
                pass
            if not args.no_browser:
                webbrowser.open(f"http://{HOST}:{PORT}/")
            print("Existing AtlasFind panel found; worker restart requested.")
            return
        except OSError:
            pass
    if args.start_worker:
        start_worker()
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    if not args.no_browser and os.environ.get("ATLASFIND_NO_BROWSER") != "1":
        threading.Timer(1.0, lambda: webbrowser.open(f"http://{HOST}:{PORT}/")).start()
    print(f"AtlasFind review panel: http://{HOST}:{PORT}/ (worker={'running' if PROCESS else 'paused'})")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        if PROCESS and PROCESS.poll() is None:
            PROCESS.terminate()
        server.server_close()


if __name__ == "__main__":
    main()
