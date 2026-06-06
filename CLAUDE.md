# CLAUDE.md — Open Call Pipeline

Project memory for Claude Code when working in this repository.

## What this project is

A small, self-contained toolkit that sources **showcase / performance /
exhibition open calls** (music & sound art) and imports them into a Notion
database called **Open Call Pipeline**. It serves three applicants: **Fardian,
Yessica, and Saodor Ensemble**.

This is also packaged as an Agent Skill (see `SKILL.md`).

## Golden rules

- **Exclude residencies.** This pipeline is only for opportunities to present,
  perform, or showcase work. Never add residency calls.
- **Do not fabricate data.** Every open call must be real and verifiable. Sample
  data is clearly labelled as an example and must be replaced before importing.
- **Entry content in English.** Database entries are written in English even
  when chatting in Bahasa Indonesia.
- **Secrets stay local.** `NOTION_TOKEN` and `NOTION_DATABASE_ID` live in `.env`
  (git-ignored). Never commit `.env` or hardcode secrets.

## How to run

```bash
# 1. configure once
cp assets/.env.example .env   # then edit NOTION_TOKEN + NOTION_DATABASE_ID

# 2. validate without sending
python scripts/add_open_calls.py --dry-run

# 3. import
python scripts/add_open_calls.py            # uses open_calls.json in root
python scripts/add_open_calls.py myfile.json
```

No external dependencies — the script uses only the Python standard library
(`urllib`, `json`). Requires Python 3.8+.

## Code conventions

- Keep the importer dependency-free (stdlib only). Do not add `requests` or
  other packages.
- The list of valid select/status/multi-select options lives in the `ALLOWED`
  dict in `scripts/add_open_calls.py` and is mirrored in `references/schema.md`.
  Keep these two in sync if the Notion schema changes.
- Property names must match the Notion database exactly (case-sensitive):
  Program, Organizer, Type, Discipline, Applicant, Location, Format, Funding,
  Deadline, Fit Score, Status, Source, Link, Notes.

## Repo layout

```
open-call-pipeline/
├─ SKILL.md                  # Agent Skill manifest (name + description)
├─ CLAUDE.md                 # this file (project memory)
├─ README.md                 # human setup guide (Bahasa Indonesia)
├─ .claudeignore
├─ run.sh / run.bat          # convenience launchers
├─ requirements.txt          # intentionally empty (stdlib only)
├─ scripts/add_open_calls.py # importer
├─ references/               # schema + sourcing prompts
└─ assets/                   # sample input + .env template
```
