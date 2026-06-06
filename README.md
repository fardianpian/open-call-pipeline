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
│  └─ add_open_calls.py      # importer
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

## Troubleshooting

- **401 Unauthorized** → token salah / integration belum dihubungkan ke database.
- **404 object not found** → DATABASE_ID salah / belum di-connect.
- **validation_error pada Status** → nilai Status harus salah satu opsi standar.
- **Select baru muncul** → nilai di luar daftar dibuat otomatis; pakai ejaan persis.
