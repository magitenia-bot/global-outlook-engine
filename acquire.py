#!/usr/bin/env python3
"""Monitor sources concurrently; preserve source state and observation history.

Change detection is a discovery signal, NOT view verification or interpretation.
GitHub stores the raw record; ChatGPT owns investment stances and HTML.
"""
import argparse
import csv
import datetime as dt
import hashlib
import json
import re
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser
from pathlib import Path


EVENT_FIELDS = ['checked_at_utc', 'source_id', 'institution_id', 'result',
                'http_status', 'content_hash', 'candidate_links_json', 'error']


class Extract(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.skip = 0
        self.words = []
        self.links = []
        self.href = None

    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style', 'noscript'):
            self.skip += 1
        if tag == 'a':
            self.href = dict(attrs).get('href')

    def handle_endtag(self, tag):
        if tag in ('script', 'style', 'noscript'):
            self.skip = max(0, self.skip - 1)
        if tag == 'a':
            self.href = None

    def handle_data(self, data):
        if not self.skip and data.strip():
            self.words.append(data.strip())
            if self.href:
                self.links.append((data.strip(), self.href))


def read_csv(path):
    if not path.exists():
        return []
    with path.open(newline='', encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))


def write_csv(path, fields, rows):
    temp = path.with_suffix('.tmp')
    with temp.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
        w.writeheader()
        w.writerows(rows)
    temp.replace(path)


def monitor(source, now, timeout):
    s = source.copy()
    event = {'checked_at_utc': now, 'source_id': s.get('source_id', ''),
             'institution_id': s.get('institution_id', ''), 'result': '',
             'http_status': '', 'content_hash': '', 'candidate_links_json': '[]', 'error': ''}
    previous = s.get('last_content_hash', '')
    try:
        req = urllib.request.Request(
            s['source_url'], headers={
                'User-Agent': 'Mozilla/5.0 (compatible; GlobalOutlookSourceMonitor/3.2)',
                'Accept': 'text/html,application/xhtml+xml,application/pdf',
            })
        with urllib.request.urlopen(req, timeout=timeout) as response:
            event['http_status'] = str(response.status)
            raw = response.read(2_000_001)
            content_type = response.headers.get('Content-Type', '')
        if len(raw) > 2_000_000:
            raise ValueError('content_exceeds_limit')
        pdf = ('pdf' in content_type.lower() or
               s['source_url'].lower().split('?')[0].endswith('.pdf'))
        if pdf:
            normalized = raw
            links = [{'text': s.get('source_name', 'PDF source'), 'href': s['source_url']}]
        elif 'html' in content_type.lower():
            parser = Extract()
            parser.feed(raw.decode('utf-8', errors='replace'))
            normalized = re.sub(r'\s+', ' ', ' '.join(parser.words)).strip().encode()
            links = [{'text': t[:120], 'href': href} for t, href in parser.links
                     if re.search(r'outlook|monthly|weekly|quarterly|commentary|investment|research|pdf|'
                                  r'投資|市場|展望|投资|市场', t + ' ' + href, re.I)][:60]
        else:
            raise ValueError('unexpected_content_type: ' + content_type[:80])
        digest = hashlib.sha256(normalized).hexdigest()
        event['content_hash'] = digest
        event['candidate_links_json'] = json.dumps(links, ensure_ascii=False)
        event['result'] = ('changed_requires_review' if previous and previous != digest
                           else 'unchanged' if previous
                           else 'baseline_requires_review')
        s['last_content_hash'] = digest
        s['last_success_at_utc'] = now
        s['last_result'] = event['result']
    except Exception as exc:
        event['result'] = 'error'
        event['error'] = type(exc).__name__ + ': ' + str(exc)[:250]
        s['last_result'] = 'error'
    s['last_checked_at_utc'] = now
    return s, event


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dir', default='.')
    ap.add_argument('--timeout', type=int, default=9)
    ap.add_argument('--workers', type=int, default=6)
    args = ap.parse_args()
    root = Path(args.dir)
    now = dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')
    original = read_csv(root / 'sources.csv')
    if not original:
        raise RuntimeError('sources.csv is empty or missing: monitoring aborted to prevent data loss')
    history = read_csv(root / 'acquisition_events.csv')
    active = [s for s in original if s.get('status') == 'active']
    checked = {}
    with ThreadPoolExecutor(max_workers=max(1, min(args.workers, 10))) as pool:
        for result, event in pool.map(lambda s: monitor(s, now, args.timeout), active):
            checked[result['source_id']] = result
            history.append(event)
            print(event['source_id'], event['result'], flush=True)
    updated = [checked.get(s.get('source_id'), s) for s in original]
    write_csv(root / 'sources.csv', list(original[0]), updated)
    write_csv(root / 'acquisition_events.csv', EVENT_FIELDS, history)
    print('Monitoring complete. Sources checked:', len(active),
          'observations retained:', len(history),
          'investment stances inferred: 0')


if __name__ == '__main__':
    main()
