#!/usr/bin/env python3
"""
Instagram Open Call Scraper
Menelusuri hashtag & akun IG untuk pengumuman open call, lalu menghasilkan
open_calls_instagram.json yang siap diimpor ke Notion via add_open_calls.py.

Penggunaan:
    python scripts/instagram_scrape.py
    python scripts/instagram_scrape.py --dry-run
    python scripts/instagram_scrape.py --max-posts=30

Konfigurasi di .env:
    IG_USERNAME  = username Instagram (opsional, tapi sangat dianjurkan)
    IG_PASSWORD  = password Instagram (opsional)

Membutuhkan: pip install instaloader
"""

import json
import os
import re
import sys
from datetime import datetime, timezone, timedelta

try:
    import instaloader
except ImportError:
    sys.exit(
        "❌ Instaloader belum terinstall.\n"
        "   Jalankan: .venv/bin/pip install instaloader"
    )

import pipeline_log

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---------------------------------------------------------------------------
# Konfigurasi sumber
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

# Akun-akun organisasi seni yang sering posting open call.
# Tambahkan username (tanpa @) sesuai kebutuhan.
IG_ACCOUNTS = [
    "classicalnext",
    "womex_official",
    "ims_media",           # International Music Summit
    "newmusicusa",
    "icmc_sounds",
    "spatialmedialabs",
    "cimeba_music",
    "artsmusicberlin",
]

# ---------------------------------------------------------------------------
# Filter kata kunci
# ---------------------------------------------------------------------------

OPEN_CALL_KEYWORDS = [
    "open call", "call for", "call for submissions", "call for entries",
    "call for works", "call for artists", "apply now", "applications open",
    "deadline", "submit your", "we are accepting", "accepting submissions",
    "accepting applications", "submit by", "entries open",
]

RESIDENCY_KEYWORDS = [
    "residency", "artist-in-residence", "artist in residence",
    "residência", "residenz",
]

INTL_INDICATORS = [
    "international", "worldwide", "global", "open to all",
    "all countries", "artists worldwide", "open internationally",
    "artists from anywhere",
]

GEO_RESTRICT_KEYWORDS = [
    "us citizens only", "uk only", "eu only", "european citizens",
    "american citizens only", "british citizens only",
    "australian citizens only", "residents only",
    "must be based in", "must reside in",
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


def is_open_call(caption: str) -> bool:
    lower = caption.lower()
    return any(kw in lower for kw in OPEN_CALL_KEYWORDS)


def is_residency(caption: str) -> bool:
    lower = caption.lower()
    return any(kw in lower for kw in RESIDENCY_KEYWORDS)


def is_eligible(caption: str) -> bool:
    lower = caption.lower()
    if any(kw in lower for kw in GEO_RESTRICT_KEYWORDS):
        return any(kw in lower for kw in INTL_INDICATORS)
    return True


def extract_deadline(caption: str):
    """Coba ekstrak tanggal deadline dari teks caption. Return 'YYYY-MM-DD' atau None."""
    patterns = [
        r'deadline[:\s]+(\d{4}-\d{2}-\d{2})',
        r'deadline[:\s]+(\w+ \d{1,2},?\s+\d{4})',
        r'deadline[:\s]+(\d{1,2}[\./]\d{1,2}[\./]\d{4})',
        r'by\s+(\w+ \d{1,2},?\s+\d{4})',
        r'closes?\s+(\w+ \d{1,2},?\s+\d{4})',
        r'due[:\s]+(\w+ \d{1,2},?\s+\d{4})',
        r'(\d{4}-\d{2}-\d{2})',
        r'(\d{1,2}[\./]\d{1,2}[\./]\d{4})',
    ]
    formats = [
        "%Y-%m-%d", "%B %d, %Y", "%B %d %Y", "%b %d, %Y", "%b %d %Y",
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
                if parsed.year < 2025:
                    continue
                return parsed.strftime("%Y-%m-%d")
            except ValueError:
                continue
    return None


def extract_external_link(caption: str, fallback: str) -> str:
    urls = re.findall(r'https?://[^\s\)>\]]+', caption)
    external = [u for u in urls if "instagram.com" not in u]
    return external[0] if external else fallback


def build_title(caption: str, username: str) -> str:
    first = caption.split("\n")[0].strip()
    clean = re.sub(r"#\w+", "", first).strip()
    clean = re.sub(r"\s+", " ", clean).strip("•·–—- ")
    if len(clean) > 90:
        clean = clean[:87] + "..."
    return clean or f"Open Call via @{username}"


def fit_score(caption: str) -> int:
    lower = caption.lower()
    score = 2
    if any(k in lower for k in SOUND_HIGH):
        score = 4
    elif any(k in lower for k in SOUND_MED):
        score = 3
    funded = any(k in lower for k in ["funded", "fee waived", "no fee", "no submission fee"])
    if funded:
        score = min(score + 1, 5)
    return score


def post_to_entry(post) -> dict:
    caption = post.caption or ""
    username = post.owner_username
    post_url = f"https://www.instagram.com/p/{post.shortcode}/"

    deadline = extract_deadline(caption)
    notes_caption = caption[:400].replace("\n", " ")

    entry = {
        "Program": build_title(caption, username),
        "Organizer": f"@{username}",
        "Type": "Call for Works",
        "Discipline": "Sound Art",
        "Applicant": ["Fardian", "Yessica", "Saodor Ensemble"],
        "Location": "TBD — verify on source",
        "Format": "In-person",
        "Funding": "Fee-free",
        "Fit Score": fit_score(caption),
        "Status": "New",
        "Source": "Instagram",
        "Link": extract_external_link(caption, post_url),
        "Notes": f"IG @{username} | {post_url} | Caption: {notes_caption}",
    }
    if deadline:
        entry["Deadline"] = deadline
    return entry


# ---------------------------------------------------------------------------
# Login helper
# ---------------------------------------------------------------------------

def login(L: instaloader.Instaloader):
    username = os.environ.get("IG_USERNAME", "").strip()
    password = os.environ.get("IG_PASSWORD", "").strip()
    if not username or not password:
        print(
            "ℹ️  Tidak ada IG_USERNAME/IG_PASSWORD di .env.\n"
            "   Rate limit tanpa login: ~50 req/jam (hashtag terbatas).\n"
        )
        return
    try:
        session_file = os.path.join(ROOT, f".instaloader_session_{username}")
        if os.path.exists(session_file):
            L.load_session_from_file(username, session_file)
            print(f"✅ Session dimuat untuk @{username}")
        else:
            L.login(username, password)
            L.save_session_to_file(session_file)
            print(f"✅ Login berhasil sebagai @{username}")
    except Exception as e:
        print(f"⚠️  Login gagal: {e}\n   Melanjutkan tanpa login.")


# ---------------------------------------------------------------------------
# Scraper utama
# ---------------------------------------------------------------------------

def scrape_hashtag(L, tag: str, max_posts: int, seen: set, cutoff_days: int) -> list:
    results = []
    cutoff = datetime.now(timezone.utc) - timedelta(days=cutoff_days)
    count = 0
    print(f"\n  #{tag} ...")
    try:
        ht = instaloader.Hashtag.from_name(L.context, tag)
        for post in ht.get_posts():
            if count >= max_posts:
                break
            count += 1
            try:
                if post.shortcode in seen:
                    continue
                if post.date_utc < cutoff:
                    break
                seen.add(post.shortcode)
                caption = post.caption or ""
                if not is_open_call(caption):
                    continue
                if is_residency(caption):
                    print(f"    ⏭ residency skip: {post.shortcode}")
                    continue
                if not is_eligible(caption):
                    print(f"    ⏭ eligibility skip: {post.shortcode}")
                    continue
                entry = post_to_entry(post)
                results.append(entry)
                print(f"    ✅ {entry['Program'][:65]}")
            except Exception as exc:
                print(f"    ⚠️ post error: {exc}")
    except Exception as exc:
        print(f"    ❌ gagal scrape #{tag}: {exc}")
    return results


def scrape_account(L, username: str, max_posts: int, seen: set, cutoff_days: int) -> list:
    results = []
    cutoff = datetime.now(timezone.utc) - timedelta(days=cutoff_days)
    count = 0
    print(f"\n  @{username} ...")
    try:
        profile = instaloader.Profile.from_username(L.context, username)
        for post in profile.get_posts():
            if count >= max_posts:
                break
            count += 1
            try:
                if post.shortcode in seen:
                    continue
                if post.date_utc < cutoff:
                    break
                seen.add(post.shortcode)
                caption = post.caption or ""
                if not is_open_call(caption):
                    continue
                if is_residency(caption):
                    print(f"    ⏭ residency skip: {post.shortcode}")
                    continue
                if not is_eligible(caption):
                    print(f"    ⏭ eligibility skip: {post.shortcode}")
                    continue
                entry = post_to_entry(post)
                results.append(entry)
                print(f"    ✅ {entry['Program'][:65]}")
            except Exception as exc:
                print(f"    ⚠️ post error: {exc}")
    except Exception as exc:
        print(f"    ❌ gagal scrape @{username}: {exc}")
    return results


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    load_env()

    dry_run = "--dry-run" in sys.argv
    max_posts = 25
    cutoff_days = 60
    for arg in sys.argv[1:]:
        if arg.startswith("--max-posts="):
            max_posts = int(arg.split("=")[1])
        if arg.startswith("--days="):
            cutoff_days = int(arg.split("=")[1])

    print("=" * 60)
    print("📸 Instagram Open Call Scraper")
    print(f"   Max posts per sumber : {max_posts}")
    print(f"   Rentang waktu        : {cutoff_days} hari terakhir")
    print(f"   Mode                 : {'dry-run' if dry_run else 'normal'}")
    print("=" * 60)

    L = instaloader.Instaloader(
        download_pictures=False,
        download_videos=False,
        download_video_thumbnails=False,
        download_comments=False,
        save_metadata=False,
        quiet=True,
    )
    login(L)

    seen = set()
    all_entries = []

    print("\n── Hashtags ─────────────────────────────────────────")
    for tag in HASHTAGS:
        entries = scrape_hashtag(L, tag, max_posts, seen, cutoff_days)
        all_entries.extend(entries)

    if IG_ACCOUNTS:
        print("\n── Akun Organisasi ──────────────────────────────────")
        for account in IG_ACCOUNTS:
            entries = scrape_account(L, account, max_posts, seen, cutoff_days)
            all_entries.extend(entries)

    print(f"\n{'─' * 60}")
    print(f"Total ditemukan: {len(all_entries)} open call\n")

    if not all_entries:
        print("⚠️  Tidak ada open call yang memenuhi filter.")
        return

    if dry_run:
        print("🧪 dry-run — tidak menulis file.")
        for i, e in enumerate(all_entries, 1):
            print(f"  [{i}] {e['Program']} | Deadline: {e.get('Deadline', '-')} | Score: {e['Fit Score']}")
        return

    out_path = os.path.join(ROOT, "open_calls_instagram.json")
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(all_entries, fh, ensure_ascii=False, indent=2)

    pipeline_log.record(
        "scrape:instagram",
        hashtags=HASHTAGS,
        accounts=IG_ACCOUNTS,
        max_posts_per_source=max_posts,
        days_window=cutoff_days,
        entries_found=len(all_entries),
        output_file="open_calls_instagram.json",
        status="ok",
    )

    print(f"✅ Tersimpan: open_calls_instagram.json ({len(all_entries)} entri)")
    print()
    print("▶️  Langkah selanjutnya:")
    print("   1. Tinjau open_calls_instagram.json — verifikasi manual setiap link")
    print("   2. python scripts/add_open_calls.py open_calls_instagram.json --dry-run")
    print("   3. python scripts/add_open_calls.py open_calls_instagram.json")


if __name__ == "__main__":
    main()
