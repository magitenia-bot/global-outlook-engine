#!/usr/bin/env python3
"""Global Outlook 3.1 - conservative outlook selection (stdlib only).
Ranks candidates for human verification; never certifies a document or stance.
"""
import argparse
import calendar
import csv
import datetime as dt
import re
from pathlib import Path
from urllib.parse import urlsplit

WEEKLY = re.compile(r'\b(weekly|week ahead|week in review|market recap|weekly commentary|this week)\b', re.I)
MONTHLY = re.compile(r'\b(monthly|month ahead|investment views|global investment views|monthly outlook)\b', re.I)
RELEVANT = re.compile(r'\b(outlook|investment views?|market (recap|commentary|updates?)|asset allocation|strategy|forecast|perspectives|weekly|monthly)\b', re.I)
GENERIC = re.compile(r'^(skip to|read more|here|discover more|insights|podcasts?|contact|login|sign in|privacy|about us|subscribe|home|logo|cookie|careers|sustainability)$', re.I)
FIELDS = ['source_id','institution_name','candidate_title','candidate_url','final_url','frequency_bucket','http_status','content_type','metadata_publication_date','date_evidence','date_assessment','relevance_assessment','selection_status','checked_at_utc','review_status']

def cutoff_3_months(today):
    month = today.month - 3
    year = today.year
    if month <= 0:
        month += 12
        year -= 1
    return dt.date(year, month, min(today.day, calendar.monthrange(year, month)[1]))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dir', default='.')
    args = ap.parse_args()
    root = Path(args.dir)
    source = root / 'document_verification.csv'
    if not source.exists():
        raise SystemExit('Missing document_verification.csv; run verification first')
    with source.open(newline='', encoding='utf-8-sig') as fh:
        reader = csv.DictReader(fh)
        required = {'candidate_url', 'candidate_title', 'review_status', 'metadata_publication_date'}
        if not required.issubset(set(reader.fieldnames or [])):
            raise SystemExit('Verification CSV schema mismatch; no output written')
        rows = list(reader)
    today = dt.datetime.now(dt.timezone.utc).date()
    cutoff = cutoff_3_months(today)
    results = []
    for entry in rows:
        title = (entry.get('candidate_title') or '').strip()
        url = (entry.get('final_url') or entry.get('candidate_url') or '').strip()
        combined = title + ' ' + urlsplit(url).path.replace('-', ' ')
        bucket = 'weekly' if WEEKLY.search(combined) else 'monthly' if MONTHLY.search(combined) else 'unclassified'
        generic = bool(GENERIC.fullmatch(title)) or not RELEVANT.search(combined)
        relevant = 'generic_or_unrelated' if generic else 'candidate_relevant_unverified'
        raw_date = (entry.get('metadata_publication_date') or '').strip()
        date_status = 'no_publication_date'
        if re.fullmatch(r'\d{4}-\d{2}-\d{2}', raw_date):
            try:
                parsed = dt.date.fromisoformat(raw_date)
                date_status = 'within_3_calendar_months_metadata_only' if cutoff <= parsed <= today else 'outside_window_or_future'
            except ValueError:
                date_status = 'invalid_date'
        http = (entry.get('http_status') or '').strip()
        if http != '200':
            selection = 'exclude_unreachable'
        elif generic:
            selection = 'exclude_generic_or_unrelated'
        elif date_status == 'outside_window_or_future':
            selection = 'exclude_outside_window'
        elif date_status == 'within_3_calendar_months_metadata_only':
            selection = 'priority_manual_review'
        else:
            selection = 'manual_date_review'
        result = {key: entry.get(key, '') for key in FIELDS}
        result.update(candidate_url=entry.get('candidate_url',''), frequency_bucket=bucket,
                      date_assessment=date_status, relevance_assessment=relevant,
                      selection_status=selection)
        results.append(result)
    # Deterministic; keep complete audit rows, including exclusions.
    results.sort(key=lambda r: (r['institution_name'].lower(), r['source_id'], r['candidate_url']))
    def write(name, items):
        with (root / name).open('w', newline='', encoding='utf-8') as fh:
            writer = csv.DictWriter(fh, fieldnames=FIELDS, extrasaction='ignore')
            writer.writeheader(); writer.writerows(items)
    write('outlook_selection.csv', results)
    for kind in ('weekly', 'monthly'):
        write(f'outlook_{kind}_candidates.csv', [r for r in results if r['frequency_bucket'] == kind and r['selection_status'] in ('priority_manual_review','manual_date_review')])
    print(f'Outlook selection: {len(results)} archived records; window {cutoff} to {today}.')
    for status in ('priority_manual_review', 'manual_date_review', 'exclude_generic_or_unrelated', 'exclude_outside_window', 'exclude_unreachable'):
        print(f'  {status}: {sum(r["selection_status"] == status for r in results)}')
    print('No publication dates or investment stances certified; outputs are review queues only.')

if __name__ == '__main__':
    main()
