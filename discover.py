#!/usr/bin/env python3
"""Global Outlook: multi-frequency document-link discovery, without view inference.

Every observed document is a candidate only. Preserve historical candidates and
checks; never modify validated_views.csv, the final HTML or report_status.json.
"""
import argparse
import csv
import datetime as dt
import html.parser
import re
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

KEYWORDS = re.compile(
    r'outlook|weekly|monthly|quarterly|investment views?|allocation|strategy|'
    r'commentary|insights|research|perspectives?|market review|'
    r'prospettive|mercati|investimenti|ausblick|marktkommentar|'
    r'投資|市場|展望|運用|月報|四半期|投资|市场|展望|投资策略|'
    r'अर्थव्यवस्था|बाज़ार', re.I)
SKIP = re.compile(r'privacy|cookie|terms|login|sign.in|contact|careers|subscribe|javascript:|logout', re.I)
FIELDS = ['discovered_at_utc', 'source_id', 'institution_name', 'source_page_url',
          'candidate_title', 'candidate_url', 'publication_date', 'document_verified', 'review_status']
CHECK_FIELDS = ['checked_at_utc', 'source_id', 'result', 'candidate_count', 'detail']


def load(path):
    if not path.exists():
        return []
    with path.open(newline='', encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))


def save(path, fields, rows):
    temp = path.with_suffix('.tmp')
    with temp.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
        w.writeheader()
        w.writerows(rows)
    temp.replace(path)


class Links(html.parser.HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links = []
        self.current = None

    def handle_starttag(self, tag, attrs):
        if tag.lower() == 'a':
            self.current = {'href': dict(attrs).get('href', ''), 'text': []}

    def handle_data(self, data):
        if self.current is not None:
            self.current['text'].append(data)

    def handle_endtag(self, tag):
        if tag.lower() == 'a' and self.current is not None:
            self.links.append((self.current['href'], ' '.join(self.current['text']).strip()))
            self.current = None


def candidate(src, url, title, when, status):
    return {
        'discovered_at_utc': when,
        'source_id': src.get('source_id', ''),
        'institution_name': src.get('institution_name', ''),
        'source_page_url': src.get('source_url', ''),
        'candidate_title': title[:240],
        'candidate_url': url,
        'publication_date': '',
        'document_verified': 'no',
        'review_status': status,
    }


def inspect(src, when):
    sid = src.get('source_id', '')
    url = src.get('source_url', '').strip()
    items = []
    check = {'checked_at_utc': when, 'source_id': sid,
             'result': 'ok', 'candidate_count': 0, 'detail': ''}
    try:
        if urllib.parse.urlsplit(url).path.lower().endswith('.pdf'):
            items.append(candidate(src, url, src.get('source_name') or 'PDF outlook',
                                   when, 'candidate_pdf_unverified'))
            check['result'] = 'pdf_candidate'
        else:
            req = urllib.request.Request(
                url, headers={'User-Agent': 'Mozilla/5.0 (compatible; GlobalOutlookResearch/3.2)',
                              'Accept': 'text/html,application/xhtml+xml'})
            with urllib.request.urlopen(req, timeout=9) as res:
                ctype = res.headers.get('Content-Type', '')
                if 'html' not in ctype.lower():
                    raise ValueError('non_html_source: ' + ctype[:60])
                raw = res.read(1500001)
                if len(raw) > 1500000:
                    raise ValueError('html_too_large')
                final = res.geturl()
                charset = res.headers.get_content_charset() or 'utf-8'
            page = raw.decode(charset, errors='replace')
            parser = Links()
            parser.feed(page)
            items.append(candidate(src, final, src.get('source_name') or 'Research landing page',
                                   when, 'source_page_unverified'))
            seen = {final}
            for href, title in parser.links:
                href = (href or '').strip()
                target = urllib.parse.urljoin(final, href)
                parts = urllib.parse.urlsplit(target)
                if parts.scheme not in ('http', 'https') or not parts.hostname:
                    continue
                target = urllib.parse.urlunsplit(parts._replace(fragment=''))
                if target in seen or SKIP.search(target) or SKIP.search(title):
                    continue
                if not (KEYWORDS.search(title + ' ' + parts.path) or parts.path.lower().endswith('.pdf')):
                    continue
                # Only same-site or PDF links to third-party document hosts.
                site = urllib.parse.urlsplit(final).hostname or ''
                if not (parts.hostname == site or parts.hostname.endswith('.' + site)
                        or parts.path.lower().endswith('.pdf')):
                    continue
                seen.add(target)
                items.append(candidate(src, target, re.sub(r'\s+', ' ', title or parts.path),
                                       when, 'candidate_unverified'))
                if len(items) >= 41:
                    break
        check['candidate_count'] = len(items)
    except Exception as exc:
        check['result'] = 'error'
        check['detail'] = type(exc).__name__ + ': ' + str(exc)[:180]
    return items, check


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dir', default='.')
    args = ap.parse_args()
    root = Path(args.dir)
    now = dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')
    sources = [s for s in load(root / 'sources.csv')
               if s.get('status', 'active').lower() == 'active']
    results = []
    checks = []
    with ThreadPoolExecutor(max_workers=6) as pool:
        for candidates, checked in pool.map(lambda src: inspect(src, now), sources):
            results.extend(candidates)
            print(checked['source_id'], checked['result'], checked['candidate_count'], flush=True)
            # Store all checks, including HTTP failures. No technical-access veto.
            checks.append(checked)

    existing = load(root / 'document_candidates.csv')
    seen = {(x.get('source_id', ''), x.get('candidate_url', '')) for x in existing}
    new_count = 0
    for r in results:
        key = (r.get('source_id', ''), r.get('candidate_url', ''))
        if key not in seen:
            existing.append(r)
            seen.add(key)
            new_count += 1
    save(root / 'document_candidates.csv', FIELDS, existing)
    previous_checks = load(root / 'discovery_checks.csv')
    previous_checks.extend(checks)
    save(root / 'discovery_checks.csv', CHECK_FIELDS, previous_checks)
    print('Sources:', len(sources), 'new candidates:', new_count,
          'historical candidates:', len(existing), 'verified investment views: 0')


if __name__ == '__main__':
    main()
