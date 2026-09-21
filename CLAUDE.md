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
- **Eligibility filter.** Only include open calls that are open to international
  applicants (worldwide) OR specifically welcoming Indonesian artists. Skip calls
  restricted to citizens/residents of countries that exclude Indonesia.
- **Do not fabricate data.** Every open call must be real and verifiable. Sample
  data is clearly labelled as an example and must be replaced before importing.
- **Entry content in English.** Database entries are written in English even
  when chatting in Bahasa Indonesia.
- **Secrets stay local.** `NOTION_TOKEN`, `NOTION_DATABASE_ID`, and
  `APIFY_TOKEN` live in `.env` (git-ignored). Never commit `.env` or
  hardcode secrets.

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
  Deadline, Fit Score, Status, Source, Link, Notes, Date Added.

## Repo layout

```
open-call-pipeline/
├─ SKILL.md                  # Agent Skill manifest (name + description)
├─ CLAUDE.md                 # this file (project memory)
├─ README.md                 # human setup guide (Bahasa Indonesia)
├─ .claudeignore
├─ run.sh / run.bat          # convenience launchers
├─ requirements.txt          # intentionally empty (stdlib only)
├─ scripts/
│  ├─ add_open_calls.py      # importer (Notion)
│  ├─ instagram_scrape.py    # sourcing: Apify Instagram hashtag/profile scraper
│  ├─ pipeline_log.py        # shared helper: writes pipeline_history.json
│  └─ show_log.py            # prints pipeline_history.json as a table
├─ references/               # schema + sourcing prompts
└─ assets/                   # sample input + .env template
```

## Instagram sourcing (`scripts/instagram_scrape.py`)

- Uses the Apify `instagram-hashtag-scraper` actor (requires `APIFY_TOKEN` in
  `.env`, see `assets/.env.example`). Stdlib only — same dependency-free rule
  applies.
- `--dry-run` must work without `APIFY_TOKEN` set (it only prints what would
  run); don't reintroduce a hard token check ahead of the dry-run branch.
- Applies the same golden rules as the importer: excludes residencies,
  filters for international/Indonesia-eligible calls, writes
  `open_calls_instagram.json` for review before importing with
  `add_open_calls.py`.
- Both `instagram_scrape.py` and `add_open_calls.py` log every run via
  `pipeline_log.record(...)` to `pipeline_history.json` (git-ignored); view
  history with `python scripts/show_log.py`.
