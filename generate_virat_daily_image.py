#!/usr/bin/env python3
"""Generate a daily Virat Kohli cricket-stat SVG card with watermark 'Saiverse18'."""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import html
import json
import pathlib
import re
import sys
import urllib.request
from html.parser import HTMLParser

PLAYER_NAME = "Virat Kohli"
PLAYER_ID = 253802
WATERMARK = "Saiverse18"
STATSGURU_URL = (
    "https://stats.espncricinfo.com/ci/engine/player/253802.html"
    "?class={match_class};template=results;type=batting;view=innings"
)
CLASS_MAP = {"test": 1, "odi": 2, "t20i": 3}


class TableRowParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_td = False
        self.in_th = False
        self.current = ""
        self.row: list[str] = []
        self.rows: list[list[str]] = []
        self.in_row = False

    def handle_starttag(self, tag, attrs):
        if tag == "tr":
            self.row = []
            self.in_row = True
        elif tag in ("td", "th") and self.in_row:
            if tag == "td":
                self.in_td = True
            else:
                self.in_th = True
            self.current = ""

    def handle_endtag(self, tag):
        if tag == "tr" and self.in_row:
            if self.row:
                self.rows.append(self.row)
            self.in_row = False
        elif tag in ("td", "th") and (self.in_td or self.in_th):
            text = re.sub(r"\s+", " ", self.current).strip()
            self.row.append(html.unescape(text))
            self.in_td = False
            self.in_th = False

    def handle_data(self, data):
        if self.in_td or self.in_th:
            self.current += data


def fetch_html(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", errors="ignore")


def latest_innings(match_class: int) -> dict[str, str]:
    html_doc = fetch_html(STATSGURU_URL.format(match_class=match_class))
    parser = TableRowParser()
    parser.feed(html_doc)

    header = None
    for row in parser.rows:
        if "Runs" in row and "BF" in row and "Opposition" in row:
            header = row
            continue
        if header and len(row) >= len(header):
            record = dict(zip(header, row[: len(header)]))
            if re.search(r"\d", record.get("Runs", "")):
                return {
                    "date": record.get("Start Date", "N/A"),
                    "runs": record.get("Runs", "N/A"),
                    "balls": record.get("BF", "N/A"),
                    "sr": record.get("SR", "N/A"),
                    "opposition": record.get("Opposition", "N/A"),
                    "ground": record.get("Ground", "N/A"),
                    "format": next((k.upper() for k, v in CLASS_MAP.items() if v == match_class), "N/A"),
                }
    raise RuntimeError("Could not parse latest innings from Statsguru")


def build_svg(card_date: str, innings: dict[str, dict[str, str]], source_note: str) -> str:
    lines = [
        f"{fmt}: {d['runs']} ({d['balls']}) | SR {d['sr']} vs {d['opposition']} on {d['date']}"
        for fmt, d in innings.items()
    ]
    y = 170
    text_blocks = []
    for line in lines:
        safe = html.escape(line)
        text_blocks.append(f'<text x="40" y="{y}" font-size="28" fill="#E9ECF1">{safe}</text>')
        y += 56

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="628" viewBox="0 0 1200 628">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#102A43" />
      <stop offset="100%" stop-color="#1F4068" />
    </linearGradient>
  </defs>
  <rect width="1200" height="628" fill="url(#bg)" rx="24" />
  <text x="40" y="80" font-size="52" font-weight="700" fill="#FFFFFF">{PLAYER_NAME} - Daily Cricket Stats</text>
  <text x="40" y="120" font-size="24" fill="#C9D6E3">Date: {card_date}</text>
  {''.join(text_blocks)}
  <text x="40" y="596" font-size="18" fill="#B8C5D1">Source: {html.escape(source_note)}</text>
  <text x="1135" y="602" text-anchor="end" font-size="30" fill="#FFFFFF" opacity="0.50">{WATERMARK}</text>
</svg>'''


def load_fallback(path: pathlib.Path) -> dict[str, dict[str, str]]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output-dir", default="output", help="Where daily assets are written")
    ap.add_argument("--fallback-json", default="data/virat_seed_stats.json", help="Fallback stats JSON if live fetch is unavailable")
    args = ap.parse_args()

    today = dt.date.today().isoformat()
    out_dir = pathlib.Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    try:
        innings = {fmt: latest_innings(cls) for fmt, cls in CLASS_MAP.items()}
        source_note = "ESPNcricinfo Statsguru (player 253802)"
    except Exception as exc:
        fb = pathlib.Path(args.fallback_json)
        if not fb.exists():
            raise
        innings = load_fallback(fb)
        source_note = f"Fallback dataset: {fb} (live fetch failed: {exc})"
        print(f"WARNING: live fetch failed, using fallback: {exc}", file=sys.stderr)

    stats_json = out_dir / f"virat_daily_stats_{today}.json"
    stats_json.write_text(json.dumps(innings, indent=2), encoding="utf-8")

    svg = build_svg(today, innings, source_note)
    svg_path = out_dir / f"virat_daily_{today}.svg"
    svg_path.write_text(svg, encoding="utf-8")

    log_path = out_dir / "history.csv"
    write_header = not log_path.exists()
    with log_path.open("a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if write_header:
            w.writerow(["date", "format", "runs", "balls", "strike_rate", "opposition", "ground", "innings_date"])
        for fmt, stat in innings.items():
            w.writerow([today, fmt, stat["runs"], stat["balls"], stat["sr"], stat["opposition"], stat["ground"], stat["date"]])

    print(f"Wrote: {svg_path}")
    print(f"Wrote: {stats_json}")
    print(f"Updated: {log_path}")


if __name__ == "__main__":
    main()
