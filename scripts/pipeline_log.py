#!/usr/bin/env python3
"""
Pipeline Log — modul shared untuk mencatat riwayat setiap run pipeline.
Menyimpan data ke pipeline_history.json di root project.

Dipakai oleh instagram_scrape.py dan add_open_calls.py.
"""

import json
import os
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_FILE = os.path.join(ROOT, "pipeline_history.json")


def _load() -> list:
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, encoding="utf-8") as fh:
            try:
                return json.load(fh)
            except (json.JSONDecodeError, ValueError):
                return []
    return []


def _save(history: list):
    with open(LOG_FILE, "w", encoding="utf-8") as fh:
        json.dump(history, fh, ensure_ascii=False, indent=2)


def record(event: str, **fields):
    """
    Tambahkan satu baris ke pipeline_history.json.

    event: nama tahap, mis. "scrape:instagram" atau "import:notion"
    fields: data tambahan bebas (entries_found, entries_ok, dsb.)
    """
    history = _load()
    entry = {
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "event": event,
        **fields,
    }
    history.append(entry)
    _save(history)
    return entry
