#!/usr/bin/env python3
"""
Open Call Pipeline - importer
Menambahkan entri open call (showcase / presentasi karya) ke database Notion
"Open Call Pipeline".

Dijalankan dari root skill, contoh:
    python scripts/add_open_calls.py                # pakai open_calls.json (root)
    python scripts/add_open_calls.py myfile.json    # pakai file lain
    python scripts/add_open_calls.py --dry-run      # cek payload tanpa kirim ke Notion

Konfigurasi lewat file .env di root skill (lihat assets/.env.example):
    NOTION_TOKEN       = secret_xxx   (Internal Integration Secret)
    NOTION_DATABASE_ID = 32 hex chars (ID database Open Call Pipeline)

Tanpa dependency eksternal - hanya pustaka standar Python (urllib, json).
"""
import json
import os
import sys
import urllib.request
import urllib.error
from datetime import date
import pipeline_log

NOTION_VERSION = "2022-06-28"
API_URL = "https://api.notion.com/v1/pages"

# Root skill = folder induk dari folder scripts/.
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Properti select/status/multi_select yang valid di database.
# Nilai di luar daftar ini akan ditolak Notion, jadi script akan memperingatkan.
ALLOWED = {
    "Type": ["Showcase", "Festival", "Performance/Platform", "Exhibition",
             "Commission", "Competition", "Call for Works", "Grant"],
    "Discipline": ["Sound Art", "Music", "Performance", "Interdisciplinary"],
    "Format": ["In-person", "Remote", "Hybrid"],
    "Funding": ["Funded", "Fee-free", "Fee required"],
    "Status": ["New", "Maybe", "Applied", "Submitted", "Won", "Rejected", "Skipped"],
    "Source": ["Perplexity", "Claude Routine", "Manual", "Referral", "Instagram"],
    "Applicant": ["Fardian", "Yessica", "Saodor Ensemble"],
}


def load_env(path=".env"):
    full = os.path.join(ROOT, path)
    if os.path.exists(full):
        with open(full, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, val = line.split("=", 1)
                os.environ.setdefault(key.strip(), val.strip().strip('"').strip("'"))


def rich(text):
    return [{"type": "text", "text": {"content": str(text)[:2000]}}] if text else []


def warn_option(field, value):
    if value and value not in ALLOWED.get(field, []):
        print(f"   ⚠️  {field} = '{value}' bukan opsi standar. "
              f"Notion akan membuatnya otomatis (atau menolak jika tipe status).")


def build_properties(item):
    props = {}
    program = item.get("Program") or item.get("program")
    if not program:
        raise ValueError("setiap entri wajib punya 'Program'")
    props["Program"] = {"title": rich(program)}

    def add_text(name):
        v = item.get(name)
        if v:
            props[name] = {"rich_text": rich(v)}

    def add_select(name):
        v = item.get(name)
        if v:
            warn_option(name, v)
            props[name] = {"select": {"name": v}}

    add_text("Organizer")
    add_text("Location")
    add_text("Notes")
    add_select("Type")
    add_select("Discipline")
    add_select("Format")
    add_select("Funding")
    add_select("Source")

    applicants = item.get("Applicant")
    if applicants:
        if isinstance(applicants, str):
            applicants = [a.strip() for a in applicants.split(",") if a.strip()]
        for a in applicants:
            warn_option("Applicant", a)
        props["Applicant"] = {"multi_select": [{"name": a} for a in applicants]}

    status = item.get("Status") or "New"
    warn_option("Status", status)
    props["Status"] = {"status": {"name": status}}

    if item.get("Deadline"):
        props["Deadline"] = {"date": {"start": item["Deadline"]}}

    if item.get("Fit Score") is not None:
        props["Fit Score"] = {"number": float(item["Fit Score"])}

    if item.get("Link"):
        props["Link"] = {"url": item["Link"]}

    # Selalu isi "Date Added" dengan tanggal hari ini saat script dijalankan,
    # kecuali JSON sudah menyertakannya (untuk backfill manual).
    date_added = item.get("Date Added") or date.today().isoformat()
    props["Date Added"] = {"date": {"start": date_added}}

    return props


def post_page(token, database_id, properties):
    payload = {"parent": {"database_id": database_id}, "properties": properties}
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(API_URL, data=data, method="POST")
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", "application/json")
    req.add_header("Notion-Version", NOTION_VERSION)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))


def resolve_input(infile):
    """Cari file input: absolut -> apa adanya; relatif -> root; fallback ke sample."""
    if os.path.isabs(infile):
        return infile
    candidate = os.path.join(ROOT, infile)
    if os.path.exists(candidate):
        return candidate
    if infile == "open_calls.json":
        sample = os.path.join(ROOT, "assets", "open_calls.sample.json")
        if os.path.exists(sample):
            print("ℹ️  open_calls.json belum ada — memakai assets/open_calls.sample.json")
            return sample
    return candidate


def main():
    load_env()
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    dry_run = "--dry-run" in sys.argv
    infile = args[0] if args else "open_calls.json"

    infile_path = resolve_input(infile)
    if not os.path.exists(infile_path):
        sys.exit(f"❌ File input tidak ditemukan: {infile_path}")

    with open(infile_path, encoding="utf-8") as fh:
        items = json.load(fh)
    if isinstance(items, dict):
        items = [items]

    token = os.environ.get("NOTION_TOKEN", "").strip()
    db = os.environ.get("NOTION_DATABASE_ID", "").replace("-", "").strip()

    if not dry_run and (not token or not db):
        sys.exit("❌ NOTION_TOKEN / NOTION_DATABASE_ID belum diisi di .env")

    print(f"📥 Memproses {len(items)} entri dari {os.path.relpath(infile_path, ROOT)} ...\n")
    ok, fail = 0, 0
    for i, item in enumerate(items, 1):
        name = item.get("Program") or item.get("program") or "(tanpa judul)"
        print(f"[{i}/{len(items)}] {name}")
        try:
            props = build_properties(item)
            if dry_run:
                print("   🧪 dry-run, payload OK")
                ok += 1
                continue
            res = post_page(token, db, props)
            print(f"   ✅ dibuat: {res.get('url', '(no url)')}")
            ok += 1
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "ignore")
            print(f"   ❌ HTTP {e.code}: {body[:300]}")
            fail += 1
        except Exception as e:  # noqa
            print(f"   ❌ error: {e}")
            fail += 1

    print(f"\nSelesai. Berhasil: {ok} | Gagal: {fail}")

    if not dry_run:
        pipeline_log.record(
            "import:notion",
            input_file=os.path.relpath(infile_path, ROOT),
            entries_total=len(items),
            entries_ok=ok,
            entries_failed=fail,
            status="ok" if fail == 0 else "partial",
        )


if __name__ == "__main__":
    main()
