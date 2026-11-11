#!/usr/bin/env python3
"""Create a deterministic source-monitor snapshot for ChatGPT research.

This script does NOT interpret outlooks, label market stances, validate views,
or modify the assistant-authored HTML and status files.
"""
from __future__ import annotations

import argparse
import collections
import csv
import datetime as dt
import json
from pathlib import Path


def read_csv(path):
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def generate(root: Path):
    sources = read_csv(root / "sources.csv")
    events = read_csv(root / "acquisition_events.csv")
    candidates = read_csv(root / "document_candidates.csv")
    views = read_csv(root / "validated_views.csv")
    now = dt.datetime.now(dt.timezone.utc)
    institutions = sorted({x.get("institution_name", "").strip() for x in sources if x.get("institution_name", "").strip()})
    reviewed = sorted({x.get("institution_name", "").strip() for x in views
                       if (x.get("reviewer") or "").strip() == "ChatGPT - verifica documentale completata"})
    latest = {}
    recent = []
    for event in events:
        sid = event.get("source_id", "")
        if not sid:
            continue
        when = event.get("checked_at_utc", "")
        if sid not in latest or when >= latest[sid].get("checked_at_utc", ""):
            latest[sid] = event
        try:
            stamp = dt.datetime.fromisoformat(when.replace("Z", "+00:00"))
            if stamp.tzinfo is not None and now - dt.timedelta(days=4) <= stamp <= now:
                if event.get("result") in ("changed_requires_review", "baseline_requires_review"):
                    recent.append(event)
        except ValueError:
            pass
    seen = set()
    unique_candidates = []
    for row in reversed(candidates):
        key = (row.get("source_id", ""), row.get("candidate_url", ""))
        if not key[1] or key in seen:
            continue
        seen.add(key)
        unique_candidates.append({
            "institution_name": row.get("institution_name", ""),
            "candidate_title": row.get("candidate_title", ""),
            "candidate_url": row.get("candidate_url", ""),
            "source_page_url": row.get("source_page_url", ""),
            "discovered_at_utc": row.get("discovered_at_utc", ""),
            "review_status": row.get("review_status", "candidate_unverified"),
        })
    recent.sort(key=lambda e: e.get("checked_at_utc", ""), reverse=True)
    last_counts = collections.Counter(event.get("result", "unknown") for event in latest.values())
    data = {
        "generated_at_utc": now.isoformat(timespec="seconds"),
        "purpose": "Discovery queue for ChatGPT document interpretation and report creation; not verified investment views",
        "source_institutions": len(institutions),
        "sources_total": len(sources),
        "sources_active": sum(1 for s in sources if s.get("status") == "active"),
        "source_last_results": dict(sorted(last_counts.items())),
        "source_change_events_last_4d": len(recent),
        "source_changes_recent": [
            {"source_id": e.get("source_id"), "checked_at_utc": e.get("checked_at_utc"), "result": e.get("result"),
             "http_status": e.get("http_status"), "error": e.get("error", "")}
            for e in recent[:120]
        ],
        "candidate_documents_total": len(unique_candidates),
        "candidate_documents_recent": unique_candidates[:300],
        "views_already_recorded": len(views),
        "institutions_with_recorded_views": len(reviewed),
        "institutions_without_recorded_views": [n for n in institutions if n not in reviewed],
        "interpretation_required": True,
        "automated_view_validation_performed": False,
    }
    (root / "research_snapshot.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print("Discovery snapshot written:", data["source_institutions"], "institutions,",
          data["candidate_documents_total"], "candidate links.",
          "No investment stances generated.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=".")
    args = ap.parse_args()
    generate(Path(args.dir))
