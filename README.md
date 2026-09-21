# 🎪 Open Call Pipeline — Agent Skill

Paket siap-jalan + **Agent Skill** untuk memasukkan peluang **showcase /
presentasi karya / festival / performance / exhibition** ke database Notion
**Open Call Pipeline**. Fokus pada kesempatan menampilkan karya — **bukan
residensi**. Untuk Fardian, Yessica, & Saodor Ensemble.

## Struktur (mengikuti format Agent Skills Anthropic)

```
open-call-pipeline/
├─ SKILL.md                  # manifest skill (name + description + instruksi)
├─ CLAUDE.md                 # project memory untuk Claude Code
├─ README.md                 # panduan manusia (file ini)
├─ .claudeignore
├─ run.sh / run.bat          # peluncur
├─ requirements.txt          # kosong (hanya pustaka standar Python)
├─ scripts/
│  ├─ add_open_calls.py      # importer ke Notion
│  ├─ instagram_scrape.py    # sourcing open call dari Instagram (via Apify)
│  ├─ pipeline_log.py        # helper: catat riwayat run ke pipeline_history.json
│  └─ show_log.py            # tampilkan riwayat run sebagai tabel
├─ references/
│  ├─ schema.md              # referensi field + opsi valid
│  ├─ perplexity.md          # Prompt 1 (pencarian cepat)
│  └─ claude_routine.md      # Prompt 2 (routine mingguan)
└─ assets/
   ├─ open_calls.sample.json # contoh input
   └─ .env.example           # template konfigurasi
```

## Memakai sebagai Agent Skill

Salin folder `open-call-pipeline/` ke direktori skills milikmu, mis:
```bash
cp -r open-call-pipeline ~/.claude/skills/
```
Claude Code akan membaca `SKILL.md` (name + description) dan memuat instruksinya
secara otomatis saat relevan. `CLAUDE.md` menjadi project memory ketika kamu
membuka folder ini sebagai proyek.

## Memakai sebagai script biasa

### 1. Buat Notion Integration
1. Buka https://www.notion.so/my-integrations → **New integration** (Internal).
2. Salin **Internal Integration Secret**.

### 2. Hubungkan integration ke database
Buka database **Open Call Pipeline** → menu **⋯** → **Connections** → pilih
integration kamu.

### 3. Ambil DATABASE ID
Dari URL database, ambil 32 karakter hex (setelah nama, sebelum `?`).

### 4. Konfigurasi
```bash
cp assets/.env.example .env
# edit .env: NOTION_TOKEN + NOTION_DATABASE_ID
```

### 5. Jalankan
```bash
chmod +x run.sh
./run.sh --dry-run     # validasi tanpa kirim
./run.sh               # impor (default open_calls.json di root)
./run.sh data.json     # pakai file lain
```
Windows: `run.bat`, `run.bat --dry-run`.
Langsung: `python scripts/add_open_calls.py --dry-run`.

## Format data

Lihat `references/schema.md` untuk daftar field & opsi valid. Mulai dari
`assets/open_calls.sample.json`. Isi entri dalam **Bahasa Inggris**.

## Sourcing dari Instagram (opsional)

`scripts/instagram_scrape.py` mencari open call lewat hashtag/profil
Instagram memakai Apify actor `instagram-hashtag-scraper`.

1. Daftar gratis di https://apify.com (free tier: ~$5 kredit/bulan).
2. Ambil token di https://console.apify.com/account/integrations, isi
   `APIFY_TOKEN` di `.env` (lihat `assets/.env.example`).
3. Jalankan:
   ```bash
   python scripts/instagram_scrape.py --dry-run   # cek daftar hashtag, tanpa API call
   python scripts/instagram_scrape.py              # scrape sungguhan
   python scripts/instagram_scrape.py --max-posts=30
   ```
4. Hasil yang lolos filter (bukan residensi, eligible internasional/Indonesia)
   ditulis ke `open_calls_instagram.json`. Tinjau dulu sebelum diimpor:
   ```bash
   python scripts/add_open_calls.py open_calls_instagram.json --dry-run
   python scripts/add_open_calls.py open_calls_instagram.json
   ```

Setiap run `instagram_scrape.py` dan `add_open_calls.py` dicatat ke
`pipeline_history.json` (git-ignored). Lihat riwayatnya dengan:
```bash
python scripts/show_log.py            # semua riwayat
python scripts/show_log.py --last=10  # 10 run terakhir
```

## Troubleshooting

- **401 Unauthorized** → token salah / integration belum dihubungkan ke database.
- **404 object not found** → DATABASE_ID salah / belum di-connect.
- **validation_error pada Status** → nilai Status harus salah satu opsi standar.
- **Select baru muncul** → nilai di luar daftar dibuat otomatis; pakai ejaan persis.
