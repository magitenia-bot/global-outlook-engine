# Global Outlook 3.1 — Institutional dashboard

The existing GitHub Action monitors source pages, discovers candidate outlook documents, checks HTTP/metadata, and classifies candidate frequencies once daily at approximately 07:00 Europe/Rome (GitHub Actions scheduling can be delayed).

**New:** `build_report.py` generates `global_outlook.html` (responsive, Italian) and `report_status.json`, available as GitHub Actions artifacts and committed to the repository. The generated HTML is committed to the repository after successful checks. Public GitHub Pages availability depends on repository Pages settings; email delivery is not part of this workflow. No third-party packages or API keys are needed.

## Integrity rules

- `outlook_*_candidates.csv` entries are **unverified**. They never contribute to investment stances or consensus.
- The first two old admission filters (official-source requirement and technical accessibility requirement) have been removed. Sources may be primary or secondary and temporary access errors do not automatically reject a view. Each included position must still be pertinent, attributable, interpretable and traceable to research evidence.
- No independent human approval is required. Only entries in `validated_views.csv` explicitly marked `ChatGPT - verifica documentale completata` after direct document/content review enter operational semaphores; other entries remain exploratory. GitHub only stores research and generates the dashboard; it does not certify views.
- Fields: institution_name, document_url (HTTPS), publication_date (ISO date), frequency (`weekly`/`monthly`/`quarterly`), asset_class, stance (`positive`/`neutral`/`negative`), reviewed_at_utc (ISO UTC datetime), reviewer, evidence_quote, previous_stance (optional), previous_document_url (optional).
- Arrows are shown only with an explicit previous stance. Duplicate institution/asset/frequency entries use the most recently published/reviewed record.
- Consensus is an **equal-weighted descriptive summary of validated views**, not a performance forecast; source coverage and flows are labeled transparently. No automatic LLM inference or document-body certification is claimed.
- If no validated rows exist, the HTML displays `n.d.` instead of fabricated stances.

## Run locally

```sh
python build_report.py --dir .
```

## Deploy

Copy the contents of this updated repository to the existing GitHub repository, including `.github/workflows/monitor.yml`. Run the workflow once via Actions → Global Outlook - Daily Production → Run workflow. The `global-outlook-results` artifact contains `global_outlook.html` and `report_status.json`.

For a public or private web link, GitHub Pages or another authenticated hosting integration must be configured separately. GitHub Actions artifacts require GitHub access and are retained for 30 days.
