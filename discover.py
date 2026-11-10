#!/usr/bin/env python3
"""Global Outlook 3.1: conservative official-page document-link discovery.
Standard library only. Candidate links are NOT verified publications or stances.
"""
import argparse
import csv
import datetime as dt
import html.parser
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

KEYWORDS = re.compile(r'outlook|weekly|monthly|investment views?|market (views?|commentary|perspectives)|asset allocation|global views?|strategy|insights|research|prospettive|mercati|investimenti|perspectivas|perspectives|ausblick|marktkommentar', re.I)
SKIP = re.compile(r'privacy|cookie|terms|login|sign.in|contact|careers|subscribe|javascript:', re.I)
MAX_BYTES = 2_000_000

class Links(html.parser.HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links=[]; self.current=None
    def handle_starttag(self, tag, attrs):
        if tag.lower() == 'a':
            data=dict(attrs); self.current={'href':data.get('href',''), 'text':[]}
    def handle_data(self, data):
        if self.current is not None: self.current['text'].append(data)
    def handle_endtag(self, tag):
        if tag.lower() == 'a' and self.current is not None:
            self.links.append((self.current['href'], ' '.join(self.current['text']).strip()))
            self.current=None

def fetch(url):
    req=urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0 (compatible; GlobalOutlookResearch/3.1; research link discovery)', 'Accept':'text/html'})
    with urllib.request.urlopen(req, timeout=12) as res:
        ctype=res.headers.get('Content-Type','')
        if 'html' not in ctype.lower(): raise ValueError('non_html_source')
        raw=res.read(MAX_BYTES+1)
        if len(raw)>MAX_BYTES: raise ValueError('html_too_large')
        charset=res.headers.get_content_charset() or 'utf-8'
        return raw.decode(charset, errors='replace'), res.geturl()

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--dir',default='.'); args=ap.parse_args()
    root=Path(args.dir); now=dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')
    with (root/'sources.csv').open(newline='',encoding='utf-8-sig') as f: sources=list(csv.DictReader(f))
    rows=[]; checks=[]
    for s in sources:
        sid=s.get('source_id',''); url=s.get('source_url','').strip()
        if s.get('status','active').lower()!='active' or s.get('frequency','').strip().lower() != 'weekly': continue
        try:
            # A registered official PDF is itself a document candidate, not an HTML listing.
            if urllib.parse.urlsplit(url).path.lower().endswith('.pdf'):
                rows.append({'discovered_at_utc':now,'source_id':sid,'institution_name':s.get('institution_name',''),
                             'source_page_url':url,'candidate_title':s.get('source_name','') or 'Official PDF outlook',
                             'candidate_url':url,'publication_date':'','document_verified':'no',
                             'review_status':'candidate_pdf_unverified'})
                checks.append({'checked_at_utc':now,'source_id':sid,'result':'pdf_candidate','candidate_count':1,'detail':'Direct PDF: pending verification'})
                print(f'{sid}: direct PDF candidate (unverified)',flush=True)
                continue
            page,final=fetch(url); parser=Links(); parser.feed(page)
            # Official weekly landing pages can themselves contain the current edition.
            # Their publication date must still be verified downstream.
            rows.append({'discovered_at_utc':now,'source_id':sid,'institution_name':s.get('institution_name',''),
                         'source_page_url':url,'candidate_title':s.get('source_name','') or 'Weekly outlook',
                         'candidate_url':final,'publication_date':'','document_verified':'no',
                         'review_status':'weekly_source_page_unverified'})
            seen=set(); count=0
            for href,title in parser.links:
                target=urllib.parse.urljoin(final,href.strip()); parsed=urllib.parse.urlparse(target)
                if parsed.scheme not in ('http','https'): continue
                target=urllib.parse.urlunparse(parsed._replace(fragment=''))
                if target in seen or SKIP.search(target): continue
                seen.add(target)
                if not KEYWORDS.search(title+' '+parsed.path): continue
                if not re.search(r'weekly|week(?:ly)?|market recap|market commentary|market directions|market updates?',title+' '+parsed.path,re.I): continue
                rows.append({'discovered_at_utc':now,'source_id':sid,'institution_name':s.get('institution_name',''),
                             'source_page_url':url,'candidate_title':re.sub(r'\s+',' ',title)[:240],
                             'candidate_url':target,'publication_date':'','document_verified':'no',
                             'review_status':'candidate_unverified'})
                count+=1
                if count>=80: break
            checks.append({'checked_at_utc':now,'source_id':sid,'result':'ok','candidate_count':count,'detail':''})
            print(f'{sid}: {count} candidate links (unverified)',flush=True)
        except Exception as e:
            checks.append({'checked_at_utc':now,'source_id':sid,'result':'error','candidate_count':0,'detail':f'{type(e).__name__}: {str(e)[:160]}'})
            print(f'{sid}: error ({type(e).__name__})',flush=True)
    fields=['discovered_at_utc','source_id','institution_name','source_page_url','candidate_title','candidate_url','publication_date','document_verified','review_status']
    # Replace current discovery snapshot, never mutate the historical source registry.
    with (root/'document_candidates.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)
    with (root/'discovery_checks.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=['checked_at_utc','source_id','result','candidate_count','detail']); w.writeheader(); w.writerows(checks)
    print(f'Discovery complete: {len(rows)} unverified candidate links from {len(checks)} sources.',flush=True)
    print('No publication dates, documents, or investment stances have been verified.',flush=True)

if __name__=='__main__': main()
