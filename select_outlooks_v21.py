#!/usr/bin/env python3
"""Global Outlook 3.1 - Outlook Selection 2.1. Standard library only.
Conservative candidate queues; no automatic document/stance certification.
"""
import argparse
import calendar
import csv
import datetime as dt
import re
from pathlib import Path
from urllib.parse import urlsplit, unquote

FIELDS = ['source_id','institution_name','candidate_title','candidate_url','final_url','frequency_bucket','http_status','content_type','metadata_publication_date','date_evidence','date_assessment','relevance_assessment','selection_status','checked_at_utc','review_status']
WEEKLY = re.compile(r'\b(weekly|week(?:ly)? ahead|week in review|weekly commentary|weekly market|weekly update|weekly recap|weekly outlook)\b', re.I)
MONTHLY = re.compile(r'\b(monthly|month ahead|investment views|global investment views|monthly outlook|monthly market|monthly commentary)\b', re.I)
QUARTERLY = re.compile(r'\b(quarterly|quarter|q[1-4]\s*20\d{2}|quarterly outlook|trimestrale)\b', re.I)
STRATEGIC = re.compile(r'\b(annual|year ahead|long.term|secular|strategic|capital market assumptions|outlook 20\d{2}|investment outlook 20\d{2})\b', re.I)
TOPIC = re.compile(r'\b(outlook|investment views?|market (?:recap|commentary|updates?|insights?|outlook)|asset allocation|investment strategy|economic (?:outlook|forecast)|macro(?:economic)? outlook|portfolio strategy|capital market assumptions|weekly commentary|weekly update|weekly recap)\b', re.I)
BAD = re.compile(r'^(?:skip(?: to)?(?: main)? content|skip to navigation|read (?:more|the article)|click here|here|discover more|learn more|insights|investment insights|podcasts?|contact(?: us)?|log(?:in| in)|sign in|privacy(?: policy)?|about us|subscribe|home|logo|cookie(?:s)?|careers|sustainability|enterprise|don.t miss out|market insights overview|all insights|global outlook|investment views)$', re.I)
BAD_PATH = re.compile(r'/(?:login|signin|privacy|cookies?|careers|contact|subscribe|podcast|about-us)(?:/|$)', re.I)

def cutoff(today):
    month, year = today.month - 2, today.year
    if month <= 0: month, year = month + 12, year - 1
    return dt.date(year, month, min(today.day, calendar.monthrange(year, month)[1]))

def classify(row, today, start):
    title = re.sub(r'\s+', ' ', (row.get('candidate_title') or '').strip())
    url = (row.get('final_url') or row.get('candidate_url') or '').strip()
    path = unquote(urlsplit(url).path).replace('-', ' ').replace('_', ' ')
    generic = not title or bool(BAD.fullmatch(title)) or title.lower().startswith(('skip to ', 'read more', 'click here')) or bool(BAD_PATH.search(urlsplit(url).path))
    # A generic navigation anchor is excluded even when the destination URL looks relevant.
    text = title + ' ' + path
    relevant = bool(TOPIC.search(text)) and not generic
    # The visible title takes precedence; URL terms are fallback only.
    title_weekly, title_monthly = bool(WEEKLY.search(title)), bool(MONTHLY.search(title))
    if QUARTERLY.search(title):
        bucket = 'quarterly'
    elif STRATEGIC.search(title) and not title_weekly and not title_monthly:
        bucket = 'strategic'
    elif title_weekly != title_monthly:
        bucket = 'weekly' if title_weekly else 'monthly'
    else:
        path_weekly, path_monthly = bool(WEEKLY.search(path)), bool(MONTHLY.search(path))
        bucket = 'weekly' if path_weekly and not path_monthly else 'monthly' if path_monthly and not path_weekly else 'quarterly' if QUARTERLY.search(path) else 'strategic' if STRATEGIC.search(path) else 'unclassified'
    raw_date = (row.get('metadata_publication_date') or '').strip()
    date_status = 'no_publication_date'
    if raw_date:
        try:
            parsed = dt.date.fromisoformat(raw_date[:10]) if re.fullmatch(r'\d{4}-\d{2}-\d{2}(?:T.*)?', raw_date) else None
            date_status = ('within_2_calendar_months_metadata_only' if start <= parsed <= today else 'outside_window_or_future') if parsed else 'invalid_date'
        except ValueError:
            date_status = 'invalid_date'
    status = str(row.get('http_status') or '').strip()
    # Do not discard candidates for HTTP status, title relevance, or generic navigation labels.
    # Keep diagnostics for downstream review; never promote candidates to validated views.
    selection = 'manual_unclassified_review' if bucket == 'unclassified' else 'manual_date_review'
    result = {key: row.get(key, '') for key in FIELDS}
    result.update(frequency_bucket=bucket, date_assessment=date_status,
                  relevance_assessment='candidate_relevant_unverified' if relevant else 'generic_or_unrelated',
                  selection_status=selection)
    return result

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dir', default='.')
    args = parser.parse_args()
    root = Path(args.dir)
    src = root / 'document_verification.csv'
    if not src.exists(): raise SystemExit('Missing document_verification.csv; run verification first')
    with src.open(newline='', encoding='utf-8-sig') as handle:
        reader = csv.DictReader(handle)
        required = {'source_id','institution_name','candidate_title','candidate_url','http_status','metadata_publication_date'}
        if not required.issubset(reader.fieldnames or []): raise SystemExit('Verification CSV schema mismatch; no output written')
        input_rows = list(reader)
    today = dt.datetime.now(dt.timezone.utc).date()
    start = cutoff(today)
    # Preserve full audit history, but avoid duplicate queue entries from repeated checks.
    results = [classify(r, today, start) for r in input_rows]
    results.sort(key=lambda r: (r['institution_name'].casefold(), r['source_id'], r['candidate_url'], r['checked_at_utc']))
    def write(name, rows):
        with (root / name).open('w', newline='', encoding='utf-8') as handle:
            writer = csv.DictWriter(handle, fieldnames=FIELDS, extrasaction='ignore')
            writer.writeheader(); writer.writerows(rows)
    write('outlook_selection.csv', results)
    for frequency in ('weekly','monthly','quarterly','strategic','unclassified'):
        # Preserve all discovered candidates, including unreachable or generic links.\n        # They remain unverified until reviewed; never imply a successful fetch.\n        allowed = ('manual_date_review', 'manual_unclassified_review')
        candidates = [r for r in results if r['frequency_bucket'] == frequency and r['selection_status'] in allowed]
        unique = {}
        for row in candidates:
            key = (row['institution_name'].casefold(), (row['final_url'] or row['candidate_url']).strip().casefold())
            old = unique.get(key)
            if old is None or (row['selection_status'].startswith('priority_') and not old['selection_status'].startswith('priority_')):
                unique[key] = row
        write(f'outlook_{frequency}_candidates.csv', list(unique.values()))
        print(f'{frequency}: {len(unique)} unverified candidates for manual review')
    print(f'Outlook Selection 2.1: {len(results)} records evaluated, window {start} to {today}.')
    print('No dates, official documents or investment stances certified.')

if __name__ == '__main__': main()
