#!/usr/bin/env bash
# Jalankan importer dari root skill.
# Pakai: ./run.sh   |   ./run.sh open_calls.json   |   ./run.sh --dry-run
set -e
cd "$(dirname "$0")"

if ! command -v python3 >/dev/null 2>&1; then
  echo "❌ python3 tidak ditemukan. Install Python 3 dulu."
  exit 1
fi

if [ ! -f .env ]; then
  echo "⚠️  Belum ada file .env. Menyalin dari assets/.env.example ..."
  cp assets/.env.example .env
  echo "   Edit .env dan isi NOTION_TOKEN + NOTION_DATABASE_ID, lalu jalankan lagi."
  exit 1
fi

python3 scripts/add_open_calls.py "$@"
