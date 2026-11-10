# Global Outlook 3.1 — Institutional dashboard

The existing GitHub Action monitors source pages, discovers candidate outlook documents, checks HTTP/metadata, and classifies candidate frequencies every six hours.

**New:** `build_report.py` generates `global_outlook.html` (responsive, Italian) and `report_status.json`, available as GitHub Actions artifacts and committed to the repository. The dashboard is **not automatically published as a public site or emailed**. No third-party packages or API keys are needed.

## Integrity rules

- `outlook_*_candidates.csv` entries are **unverified**. They never contribute to investment stances or consensus.
- Only manually reviewed, fully populated `validated_views.csv` records are eligible for semaphore matrices. The initial file is header-only on purpose.
- Fields: institution_name, document_url (HTTPS), publication_date (ISO date), frequency (`weekly`/`monthly`), asset_class, stance (`positive`/`neutral`/`negative`), reviewed_at_utc (ISO UTC datetime), reviewer, evidence_quote, previous_stance (optional), previous_document_url (optional).
- Arrows are shown only with an explicit previous stance. Duplicate institution/asset/frequency entries use the most recently published/reviewed record.
- Consensus is an **equal-weighted descriptive summary of validated views**, not a performance forecast; source coverage and flows are labeled transparently. No automatic LLM inference or document-body certification is claimed.
- If no validated rows exist, the HTML displays `n.d.` instead of fabricated stances.

## Run locally

```sh
python build_report.py --dir .
```

## Deploy

Copy the contents of this updated repository to the existing GitHub repository, including `.github/workflows/monitor.yml`. Run the workflow once via Actions → Global Outlook 3.1 - Monitor → Run workflow. The `global-outlook-results` artifact contains `global_outlook.html` and `report_status.json`.

For a public or private web link, GitHub Pages or another authenticated hosting integration must be configured separately. GitHub Actions artifacts require GitHub access and are retained for 30 days.
