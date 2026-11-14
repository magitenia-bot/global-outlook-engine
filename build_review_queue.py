#!/usr/bin/env python3
"""Append-only Global Outlook discovery handoff.

Read GitHub monitor candidates and append unseen manager-document pairs to
research_curated/review_queue.csv. NEVER assess, invent or update investment
stances. Preserve every ChatGPT review decision and every validated dataset.
"""
import csv
import datetime as dt
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent
DOCS = ROOT / "research_monitor/discovered_documents.csv"
QUEUE = ROOT / "research_curated/review_queue.csv"
METRICS = ROOT / "research_curated/queue_monitor_metrics.json"
FIELDS = [
    "candidate_id", "batch", "priority", "found_at_utc", "manager",
    "original_title", "raw_url", "primary_url", "source_type",
    "review_status", "result", "published_date", "added_view_ids", "notes"
]
ZERO_TIME = "1970-01-01T00:00:00+00:00"


def read_csv(path):
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path, records):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)


def key(manager, url):
    return (manager.strip().casefold(), url.strip().casefold())


def status_from_metadata(doc):
    """Triage hints only: NOT stance validation or source verification."""
    manager = (doc.get("manager") or "").strip()
    title = (doc.get("title") or "").strip()
    kind = (doc.get("source_type") or "").strip()
    url = (doc.get("document_url") or "").strip()
    lower = title.lower()
    if kind == "registered_source" and not "news.google.com/rss/" in url:
        return "P1", "pending_primary_content", "Registered public source: verify content and publication date"
    if re.search(r"outlook|asset allocation|market view|portfolio strategy|investment view", lower):
        if manager.casefold() in title.casefold():
            return "P1", "pending_primary_content", "Issuer mentioned in title; still unverified"
        return "P2", "pending_attribution", "Potential issuer/title mismatch; resolve original URL"
    return "P3", "pending_screening", "Low-confidence discovery; no inferred financial view"


def main():
    old = read_csv(QUEUE)
    events = read_csv(DOCS)
    if not old:
        # An empty/missing queue must be explicitly seeded by a research
        # session; do not silently import thousands of legacy events.
        raise SystemExit("Queue baseline missing; refusing to bootstrap from the whole archive")
    cutoff = max((r.get("found_at_utc") or ZERO_TIME for r in old), default=ZERO_TIME)
    seen = {key(r.get("manager", ""), r.get("raw_url", "")) for r in old}
    used_ids = {r.get("candidate_id") for r in old}
    appended = 0
    last_event = cutoff
    for doc in sorted(events, key=lambda d: d.get("found_at_utc", "")):
        found_at = (doc.get("found_at_utc") or "").strip()
        if not found_at or found_at <= cutoff:
            continue
        if found_at > last_event:
            last_event = found_at
        manager = (doc.get("manager") or "").strip()
        url = (doc.get("document_url") or "").strip()
        if not manager or not url.startswith("https://"):
            continue
        k = key(manager, url)
        if k in seen:
            continue
        seen.add(k)
        date_compact = found_at[:10].replace("-", "")
        index = 1
        candidate_id = f"GO-{date_compact}-{index:03d}"
        while candidate_id in used_ids:
            index += 1
            candidate_id = f"GO-{date_compact}-{index:03d}"
        used_ids.add(candidate_id)
        priority, review_status, note = status_from_metadata(doc)
        old.append({
            "candidate_id": candidate_id,
            "batch": "BACKLOG",
            "priority": priority,
            "found_at_utc": found_at,
            "manager": manager,
            "original_title": (doc.get("title") or "")[:240],
            "raw_url": url,
            "primary_url": "",
            "source_type": doc.get("source_type") or "",
            "review_status": review_status,
            "result": "pending",
            "published_date": "",
            "added_view_ids": "",
            "notes": note,
        })
        appended += 1
    if appended:
        write_csv(QUEUE, old)
    data = {
        "schema_version": 1,
        "type": "source_discovery_handoff_only",
        "last_event_seen_utc": last_event,
        "total_candidates": len(old),
        "new_candidates_appended": appended,
        "batch_01_candidates": sum(r.get("batch") == "B01" for r in old),
        "unresolved": sum(r.get("result") == "pending" for r in old),
        "explicit_warning": "No candidate is a validated view without ChatGPT source reading",
    }
    text = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    if not METRICS.exists() or METRICS.read_text(encoding="utf-8") != text:
        METRICS.write_text(text, encoding="utf-8")
    print(f"Global Outlook queue: {len(old)} candidates, {appended} newly indexed, no stance assignment")


if __name__ == "__main__":
    main()
