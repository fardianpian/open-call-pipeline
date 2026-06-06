@echo off
REM Jalankan importer di Windows dari root skill.
REM Pakai: run.bat  |  run.bat open_calls.json  |  run.bat --dry-run
cd /d "%~dp0"
where python >nul 2>nul
if errorlevel 1 (
  echo python tidak ditemukan. Install Python 3 dulu.
  exit /b 1
)
if not exist .env (
  echo Belum ada file .env. Menyalin dari assets\.env.example ...
  copy assets\.env.example .env
  echo Edit .env dan isi NOTION_TOKEN + NOTION_DATABASE_ID, lalu jalankan lagi.
  exit /b 1
)
python scripts\add_open_calls.py %*
