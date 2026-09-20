#!/usr/bin/env python3
"""
Instagram Open Call Scraper — via Apify
Menjalankan Apify Instagram Hashtag Scraper actor untuk mencari open call,
lalu menyaring hasil dan menghasilkan open_calls_instagram.json.

Setup:
    1. Daftar di https://apify.com (free tier: $5 kredit/bulan)
    2. Ambil API token: https://console.apify.com/account/integrations
    3. Tambahkan APIFY_TOKEN ke .env

Penggunaan:
    python scripts/instagram_scrape.py
    python scripts/instagram_scrape.py --dry-run
    python scripts/instagram_scrape.py --max-posts=30
"""

import json
import os
import re
import sys
import time
import urllib.request
import urllib.error
import pipeline_log
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

APIFY_BASE = "https://api.apify.com/v2"
ACTOR_ID   = "apify~instagram-hashtag-scraper"

# ---------------------------------------------------------------------------
# Sumber pencarian
# ---------------------------------------------------------------------------

HASHTAGS = [
    "opencall",
    "callforartists",
    "callforsubmissions",
    "callforworks",
    "opencallmusic",
    "soundartcall",
    "callforentry",
    "musicsubmissions",
]

# Tambahkan URL profil IG organisasi seni yang rutin posting open call.
# Format: "https://www.instagram.com/username/"
IG_PROFILE_URLS = [
    # "https://www.instagram.com/classicalnext/",
    # "https://www.instagram.com/womex/",
]

# ---------------------------------------------------------------------------
# Filter kata kunci
# ---------------------------------------------------------------------------

OPEN_CALL_KEYWORDS = [
    "open call", "call for", "submissions", "apply now", "deadline",
    "application", "submit your", "we are accepting", "accepting submissions",
    "call for entries", "call for works", "entries open",
]

RESIDENCY_KEYWORDS = [
    "residency", "artist-in-residence", "artist in residence",
    "residência", "residenz",
]

INTL_INDICATORS = [
    "international", "worldwide", "global", "open to all",
    "all countries", "artists worldwide",
]

GEO_RESTRICT_KEYWORDS = [
    "us citizens only", "uk only", "eu only", "european citizens",
    "american citizens only", "must be based in", "must reside in",
    "residents only",
]

SOUND_HIGH = [
    "sound art", "electroacoustic", "experimental music", "field recording",
    "acousmatic", "contemporary music", "new music", "interdisciplinary",
    "electronic music", "acoustic ecology", "noise art",
]

SOUND_MED = [
    "music", "audio", "sonic", "acoustic", "composition",
    "performance art", "audio visual", "multimedia",
]

# ---------------------------------------------------------------------------
# Utilitas
# ---------------------------------------------------------------------------

def load_env():
    path = os.path.join(ROOT, ".env")
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, val = line.split("=", 1)
            os.environ.setdefault(key.strip(), val.strip().strip('"').strip("'"))


def apify_request(method, path, token, body=None):
    url = f"{APIFY_BASE}{path}?token={token}"
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body_txt = e.read().decode("utf-8", "ignore")
        raise RuntimeError(f"HTTP {e.code}: {body_txt[:300]}")


def run_actor(token, actor_input, timeout_sec=300):
    """Jalankan actor, poll sampai selesai, kembalikan dataset ID."""
    print(f"   ▶ Memulai actor {ACTOR_ID} ...")
    resp = apify_request("POST", f"/acts/{ACTOR_ID}/runs", token, actor_input)
    run_id = resp["data"]["id"]
    dataset_id = resp["data"]["defaultDatasetId"]
    print(f"   Run ID: {run_id}")

    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        time.sleep(8)
        status_resp = apify_request("GET", f"/acts/{ACTOR_ID}/runs/{run_id}", token)
        status = status_resp["data"]["status"]
        print(f"   Status: {status}")
        if status == "SUCCEEDED":
            return dataset_id
        if status in ("FAILED", "ABORTED", "TIMED-OUT"):
            raise RuntimeError(f"Actor run {status}")
    raise RuntimeError("Timeout menunggu actor selesai")


def fetch_dataset(token, dataset_id):
    resp = apify_request("GET", f"/datasets/{dataset_id}/items", token)
    return resp if isinstance(resp, list) else resp.get("items", [])


# ---------------------------------------------------------------------------
# Filter & konversi post → entry
# ---------------------------------------------------------------------------

def is_open_call(caption):
    lower = caption.lower()
    return any(kw in lower for kw in OPEN_CALL_KEYWORDS)


def is_residency(caption):
    lower = caption.lower()
    return any(kw in lower for kw in RESIDENCY_KEYWORDS)


def is_eligible(caption):
    lower = caption.lower()
    if any(kw in lower for kw in GEO_RESTRICT_KEYWORDS):
        return any(kw in lower for kw in INTL_INDICATORS)
    return True


def fit_score(caption):
    lower = caption.lower()
    score = 2
    if any(k in lower for k in SOUND_HIGH):
        score = 4
    elif any(k in lower for k in SOUND_MED):
        score = 3
    if any(k in lower for k in ["funded", "no fee", "fee waived", "no submission fee"]):
        score = min(score + 1, 5)
    return score


def extract_deadline(caption):
    patterns = [
        r'deadline[:\s]+(\d{4}-\d{2}-\d{2})',
        r'deadline[:\s]+(\w+ \d{1,2},?\s*\d{4})',
        r'deadline[:\s]+(\d{1,2}[\./]\d{1,2}[\./]\d{4})',
        r'by\s+(\w+ \d{1,2},?\s*\d{4})',
        r'closes?\s+(\w+ \d{1,2},?\s*\d{4})',
        r'due[:\s]+(\w+ \d{1,2},?\s*\d{4})',
        r'(\d{4}-\d{2}-\d{2})',
    ]
    formats = [
        "%Y-%m-%d", "%B %d, %Y", "%B %d %Y",
        "%b %d, %Y", "%b %d %Y",
        "%d/%m/%Y", "%m/%d/%Y", "%d.%m.%Y",
    ]
    for pattern in patterns:
        m = re.search(pattern, caption, re.IGNORECASE)
        if not m:
            continue
        raw = m.group(1).strip().rstrip(",")
        for fmt in formats:
            try:
                parsed = datetime.strptime(raw, fmt)
                if parsed.year >= 2025:
                    return parsed.strftime("%Y-%m-%d")
            except ValueError:
                continue
    return None


def extract_link(caption, post_url):
    urls = re.findall(r'https?://[^\s\)>\]]+', caption)
    external = [u for u in urls if "instagram.com" not in u]
    return external[0] if external else post_url


def post_key(item):
    """Identitas unik post untuk dedup. Fallback ke id(item) kalau item tidak
    punya id/shortCode/url sama sekali, supaya post tanpa field itu tidak
    saling dianggap duplikat satu sama lain."""
    key = item.get("id") or item.get("shortCode") or item.get("url")
    return key or id(item)


def build_title(caption, username):
    first = caption.split("\n")[0].strip()
    clean = re.sub(r"#\w+", "", first).strip()
    clean = re.sub(r"\s+", " ", clean).strip("•·–—- ")
    if len(clean) > 90:
        clean = clean[:87] + "..."
    return clean or f"Open Call via @{username}"


def post_to_entry(item):
    caption     = item.get("caption") or item.get("text") or ""
    username    = item.get("ownerUsername") or item.get("username") or "unknown"
    post_url    = item.get("url") or item.get("shortCode") or ""
    if post_url and not post_url.startswith("http"):
        post_url = f"https://www.instagram.com/p/{post_url}/"

    entry = {
        "Program":    build_title(caption, username),
        "Organizer":  f"@{username}",
        "Type":       "Call for Works",
        "Discipline": "Sound Art",
        "Applicant":  ["Fardian", "Yessica", "Saodor Ensemble"],
        "Location":   "TBD — verify on source",
        "Format":     "In-person",
        "Funding":    "Fee-free",
        "Fit Score":  fit_score(caption),
        "Status":     "New",
        "Source":     "Instagram",
        "Link":       extract_link(caption, post_url),
        "Notes":      f"IG @{username} | {post_url} | {caption[:300].replace(chr(10),' ')}",
    }
    deadline = extract_deadline(caption)
    if deadline:
        entry["Deadline"] = deadline
    return entry


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    load_env()

    dry_run   = "--dry-run" in sys.argv
    max_posts = 25
    for arg in sys.argv[1:]:
        if arg.startswith("--max-posts="):
            max_posts = int(arg.split("=")[1])

    token = os.environ.get("APIFY_TOKEN", "").strip()
    if not dry_run and not token:
        sys.exit(
            "❌ APIFY_TOKEN belum diisi di .env\n"
            "   Daftar gratis: https://apify.com\n"
            "   Token: https://console.apify.com/account/integrations"
        )

    print("=" * 60)
    print("📸 Instagram Open Call Scraper — via Apify")
    print(f"   Hashtags  : {len(HASHTAGS)} tag")
    print(f"   Max posts : {max_posts} per hashtag")
    print(f"   Mode      : {'dry-run' if dry_run else 'normal'}")
    print("=" * 60)

    all_entries = []
    seen_keys   = set()

    # Scrape per hashtag (satu actor run per hashtag agar lebih terkontrol)
    for tag in HASHTAGS:
        print(f"\n  #{tag} ...")
        if dry_run:
            print("   🧪 dry-run, skip API call")
            continue
        try:
            actor_input = {
                "hashtags":     [tag],
                "resultsLimit": max_posts,
            }
            dataset_id = run_actor(token, actor_input)
            items      = fetch_dataset(token, dataset_id)
            print(f"   {len(items)} post diambil")

            for item in items:
                caption = item.get("caption") or item.get("text") or ""
                key = post_key(item)
                if key in seen_keys:
                    continue
                seen_keys.add(key)

                if not is_open_call(caption):
                    continue
                if is_residency(caption):
                    print("   ⏭ residency skip")
                    continue
                if not is_eligible(caption):
                    print("   ⏭ eligibility skip")
                    continue

                entry = post_to_entry(item)
                all_entries.append(entry)
                print(f"   ✅ {entry['Program'][:65]}")

        except Exception as exc:
            print(f"   ❌ Error: {exc}")

    # Scrape profil (opsional)
    if IG_PROFILE_URLS and not dry_run:
        print(f"\n  Profil IG ({len(IG_PROFILE_URLS)}) ...")
        try:
            actor_input = {
                "directUrls":   IG_PROFILE_URLS,
                "resultsLimit": max_posts,
            }
            dataset_id = run_actor(token, actor_input)
            items      = fetch_dataset(token, dataset_id)
            for item in items:
                caption = item.get("caption") or item.get("text") or ""
                key = post_key(item)
                if key in seen_keys:
                    continue
                seen_keys.add(key)
                if not is_open_call(caption) or is_residency(caption):
                    continue
                if not is_eligible(caption):
                    continue
                entry = post_to_entry(item)
                all_entries.append(entry)
                print(f"   ✅ {entry['Program'][:65]}")
        except Exception as exc:
            print(f"   ❌ Error profil: {exc}")

    print(f"\n{'─' * 60}")
    print(f"Total ditemukan: {len(all_entries)} open call")

    if dry_run:
        print("🧪 dry-run selesai — tidak ada file ditulis.")
        return

    if not all_entries:
        print("⚠️  Tidak ada open call yang lolos filter.")
        pipeline_log.record(
            "scrape:instagram",
            source="apify",
            hashtags=HASHTAGS,
            entries_found=0,
            status="ok",
        )
        return

    out_path = os.path.join(ROOT, "open_calls_instagram.json")
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(all_entries, fh, ensure_ascii=False, indent=2)

    pipeline_log.record(
        "scrape:instagram",
        source="apify",
        hashtags=HASHTAGS,
        max_posts_per_hashtag=max_posts,
        entries_found=len(all_entries),
        output_file="open_calls_instagram.json",
        status="ok",
    )

    print("✅ Tersimpan: open_calls_instagram.json")
    print()
    print("▶️  Langkah selanjutnya:")
    print("   1. Tinjau open_calls_instagram.json — verifikasi link")
    print("   2. python scripts/add_open_calls.py open_calls_instagram.json --dry-run")
    print("   3. python scripts/add_open_calls.py open_calls_instagram.json")


if __name__ == "__main__":
    main()
