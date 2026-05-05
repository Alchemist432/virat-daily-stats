#!/usr/bin/env python3
from __future__ import annotations

import datetime as dt
import json
import os
import pathlib
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from generate_virat_daily_image import CLASS_MAP, WATERMARK, build_svg, latest_innings, load_fallback

ROOT = pathlib.Path(__file__).parent
OUT_DIR = ROOT / "output"
FALLBACK = ROOT / "data" / "virat_seed_stats.json"
HISTORY_FILE = OUT_DIR / "web_history.json"


def generate_stats() -> tuple[str, dict, str]:
    today = dt.date.today().isoformat()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    try:
        innings = {fmt: latest_innings(cls) for fmt, cls in CLASS_MAP.items()}
        source_note = "ESPNcricinfo Statsguru (player 253802)"
    except Exception as exc:
        innings = load_fallback(FALLBACK)
        source_note = f"Fallback dataset: {FALLBACK.name} (live fetch failed: {exc})"

    svg = build_svg(today, innings, source_note)
    name = f"virat_daily_{today}_{dt.datetime.utcnow().strftime('%H%M%S')}.svg"
    path = OUT_DIR / name
    path.write_text(svg, encoding="utf-8")

    history = []
    if HISTORY_FILE.exists():
        history = json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
    history.insert(0, {"file": name, "date": today, "source": source_note, "watermark": WATERMARK})
    HISTORY_FILE.write_text(json.dumps(history[:100], indent=2), encoding="utf-8")
    return name, innings, source_note


class Handler(BaseHTTPRequestHandler):
    def _json(self, payload: dict, code=200):
        body = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        p = urlparse(self.path)
        if p.path == "/":
            html = (ROOT / "web" / "index.html").read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(html)))
            self.end_headers()
            self.wfile.write(html)
            return
        if p.path == "/history":
            history = []
            if HISTORY_FILE.exists():
                history = json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
            return self._json({"history": history})
        if p.path.startswith("/images/"):
            fp = OUT_DIR / p.path.split("/images/", 1)[1]
            if not fp.exists():
                self.send_error(404)
                return
            data = fp.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "image/svg+xml")
            self.send_header("Content-Disposition", f'inline; filename="{fp.name}"')
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        self.send_error(404)

    def do_POST(self):
        if self.path != "/generate":
            self.send_error(404)
            return
        file_name, innings, source_note = generate_stats()
        self._json({"ok": True, "file": file_name, "image_url": f"/images/{file_name}", "innings": innings, "source": source_note})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    print(f"Open http://localhost:{port}")
    server.serve_forever()
