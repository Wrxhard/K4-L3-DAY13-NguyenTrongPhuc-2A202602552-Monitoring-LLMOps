from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

import yaml

from dashboard.metrics import build_dashboard_snapshot, load_log_records


REPO_ROOT = Path(__file__).resolve().parents[1]
PAGE = Path(__file__).with_name("index.html")
CONFIG = REPO_ROOT / "config" / "dashboard.yaml"
LOG = REPO_ROOT / "data" / "logs.jsonl"


class DashboardHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        path = urlsplit(self.path).path
        if path == "/":
            content = PAGE.read_bytes()
            content_type = "text/html; charset=utf-8"
        elif path == "/api/dashboard":
            config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
            snapshot = build_dashboard_snapshot(
                load_log_records(LOG), config, datetime.now(timezone.utc)
            )
            content = json.dumps(snapshot, ensure_ascii=False).encode("utf-8")
            content_type = "application/json; charset=utf-8"
        else:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)


def main() -> None:
    parser = argparse.ArgumentParser(description="Local Day 13 monitoring dashboard")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8501)
    args = parser.parse_args()
    print(f"Dashboard: http://{args.host}:{args.port}", flush=True)
    ThreadingHTTPServer((args.host, args.port), DashboardHandler).serve_forever()


if __name__ == "__main__":
    main()
