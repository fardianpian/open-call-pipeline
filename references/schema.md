# Schema reference — Open Call Pipeline

Input is a JSON **array of objects** (or a single object). Every entry must have
`Program`. All other fields are optional. Write content in **English**.

| Key | Notion type | Notes / allowed values |
|---|---|---|
| `Program` (required) | Title | Name of the open call / showcase |
| `Organizer` | Text | Hosting organization or platform |
| `Type` | Select | `Showcase`, `Festival`, `Performance/Platform`, `Exhibition`, `Commission`, `Competition`, `Call for Works`, `Grant` |
| `Discipline` | Select | `Sound Art`, `Music`, `Performance`, `Interdisciplinary` |
| `Applicant` | Multi-select | `Fardian`, `Yessica`, `Saodor Ensemble` (array or comma string) |
| `Location` | Text | City, country, or "Remote" |
| `Format` | Select | `In-person`, `Remote`, `Hybrid` |
| `Funding` | Select | `Funded`, `Fee-free`, `Fee required` |
| `Deadline` | Date | ISO `YYYY-MM-DD` (time optional) |
| `Fit Score` | Number | 1–5 (5 = best fit) |
| `Status` | Status | `New`, `Maybe`, `Applied`, `Submitted`, `Won`, `Rejected`, `Skipped` (default `New`) |
| `Source` | Select | `Perplexity`, `Claude Routine`, `Manual`, `Referral`, `Instagram` |
| `Link` | URL | Direct link to the open call |
| `Notes` | Text | Free notes |
| `Date Added` | Date | Diisi otomatis saat import (tanggal script dijalankan). Bisa diisi manual untuk backfill. |

## Rules

- **Exclude residencies.** Only present/perform/showcase opportunities.
- `Status` values are fixed — a non-listed value will be **rejected** by Notion.
- For `Type`, `Discipline`, `Format`, `Funding`, `Source`, `Applicant`: a
  non-listed value will be **auto-created** by Notion; use exact spelling to
  avoid duplicates. The importer prints a warning for non-standard values.

## Example

```json
[
  {
    "Program": "Sound Art Showcase 2026",
    "Organizer": "WOMEX",
    "Type": "Showcase",
    "Discipline": "Sound Art",
    "Applicant": ["Fardian", "Saodor Ensemble"],
    "Location": "Tampere, Finland",
    "Format": "In-person",
    "Funding": "Funded",
    "Deadline": "2026-07-15",
    "Fit Score": 5,
    "Status": "New",
    "Source": "Perplexity",
    "Link": "https://example.com/open-call",
    "Notes": "Replace with a real, verified opportunity before applying."
  }
]
```
