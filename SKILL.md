---
name: open-call-pipeline
description: >-
  Find and import music/sound-art SHOWCASE, festival, performance, platform,
  and exhibition open calls into the Notion "Open Call Pipeline" database for
  Fardian, Yessica, and Saodor Ensemble. Use when the user wants to discover
  opportunities to PRESENT or PERFORM work, score their fit, or push curated
  open calls into Notion. Focus on presenting/showcasing work; exclude
  residencies.
---

# Open Call Pipeline

A skill for sourcing and importing **opportunities to present or perform work**
(showcase, festival, performance/platform, exhibition, commission, competition,
call for works, grant) into the Notion **Open Call Pipeline** database.

**Applicants:** Fardian, Yessica, Saodor Ensemble.
**Scope:** opportunities to show/present/perform work. **Exclude residencies.**

## When to use this skill

Use this skill when the user asks to:
- Discover new showcase/festival/performance/exhibition open calls.
- Score how well an opportunity fits the applicants.
- Add or bulk-import open calls into the Notion database.
- Run the weekly sourcing routine.

## Workflow

1. **Source opportunities.** Run a discovery prompt from `references/`:
   - `references/perplexity.md` — quick web search for fresh open calls.
   - `references/claude_routine.md` — structured weekly routine.
   Ask the model to return results as JSON matching `references/schema.md`.

2. **Validate the JSON.** Save results to `open_calls.json` in the skill root
   (start from `assets/open_calls.sample.json`). Confirm every entry has a
   `Program` and that select/status values match `references/schema.md`.

3. **Dry-run before sending.** Run exactly:
   ```bash
   python scripts/add_open_calls.py --dry-run
   ```
   This validates payloads without writing to Notion.

4. **Import to Notion.** After configuring `.env` (see `assets/.env.example`),
   run exactly:
   ```bash
   python scripts/add_open_calls.py
   ```
   Or use a specific file: `python scripts/add_open_calls.py myfile.json`.

5. **Review in Notion.** Open the "🆕 New" view, prioritise Fit Score ≥ 4,
   check deadlines, and prepare proposals.

## Configuration

The script reads `.env` from the skill root:
- `NOTION_TOKEN` — Internal Integration Secret.
- `NOTION_DATABASE_ID` — 32-char ID of the Open Call Pipeline database.

Setup steps are in `README.md`.

## Constraints

- **Exclude residencies.** Only present/perform/showcase opportunities.
- Entry content should be written in **English**.
- Do not fabricate opportunities — every entry must be a real, verifiable call.
- Run the import commands exactly as written; do not add extra flags.

## Files

- `scripts/add_open_calls.py` — importer (Python stdlib only, no dependencies).
- `references/schema.md` — field/property reference + allowed option values.
- `references/perplexity.md`, `references/claude_routine.md` — sourcing prompts.
- `assets/open_calls.sample.json` — example input.
- `assets/.env.example` — configuration template.
