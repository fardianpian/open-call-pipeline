#!/usr/bin/env python3
"""
Show Pipeline Log — tampilkan riwayat run pipeline sebagai tabel di terminal.

Penggunaan:
    python scripts/show_log.py          # semua riwayat
    python scripts/show_log.py --last=10  # 10 run terakhir
"""

import json
import os
import sys
from datetime import datetime, timezone, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_FILE = os.path.join(ROOT, "pipeline_history.json")

WITA_OFFSET = timezone(timedelta(hours=8))

EVENT_LABEL = {
    "scrape:instagram": "Instagram Scrape",
    "import:notion":    "Notion Import",
}

STATUS_ICON = {
    "ok":      "✅",
    "partial": "⚠️ ",
    "error":   "❌",
}


def fmt_time(ts: str) -> str:
    try:
        dt = datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        local = dt.astimezone(WITA_OFFSET)
        return local.strftime("%Y-%m-%d  %H:%M WITA")
    except ValueError:
        return ts


def detail(row: dict) -> str:
    event = row.get("event", "")
    if event == "scrape:instagram":
        found = row.get("entries_found", "-")
        days = row.get("days_window", "-")
        return f"Ditemukan {found} open call | window {days}h"
    if event == "import:notion":
        ok = row.get("entries_ok", "-")
        fail = row.get("entries_failed", 0)
        src = row.get("input_file", "-")
        return f"OK {ok} | Gagal {fail} | dari {src}"
    return ""


def draw_table(rows: list):
    COL = [22, 20, 14, 54]
    headers = ["Tanggal & Waktu", "Tahap", "Status", "Detail"]

    def hr():
        print("+" + "+".join("-" * (c + 2) for c in COL) + "+")

    def row_line(cells):
        parts = []
        for cell, width in zip(cells, COL):
            cell = str(cell)
            # strip emoji for width calc (emoji = 2 chars wide but 1 len)
            display = cell.ljust(width)[:width]
            parts.append(f" {display} ")
        print("|" + "|".join(parts) + "|")

    hr()
    row_line(headers)
    hr()
    for r in rows:
        event = r.get("event", "")
        status = r.get("status", "ok")
        icon = STATUS_ICON.get(status, "  ")
        cells = [
            fmt_time(r.get("timestamp", "")),
            EVENT_LABEL.get(event, event),
            f"{icon} {status}",
            detail(r),
        ]
        row_line(cells)
    hr()


def main():
    last = None
    for arg in sys.argv[1:]:
        if arg.startswith("--last="):
            last = int(arg.split("=")[1])

    if not os.path.exists(LOG_FILE):
        print("ℹ️  Belum ada riwayat. Jalankan pipeline terlebih dahulu.")
        return

    with open(LOG_FILE, encoding="utf-8") as fh:
        history = json.load(fh)

    if not history:
        print("ℹ️  Log kosong.")
        return

    if last:
        history = history[-last:]

    print(f"\n📋 Riwayat Pipeline — {len(history)} entri\n")
    draw_table(history)
    print()


if __name__ == "__main__":
    main()
