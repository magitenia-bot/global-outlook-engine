#!/usr/bin/env python3
"""Global Outlook 3.1 - Document Verification 2.0 (stdlib only).
Evidence discovery, not certification of publication date or investment stance.
"""
import argparse
import calendar
import csv
import datetime as dt
import html.parser
import json
import re
import urllib.parse
import urllib.request
from pathlib import Path

MAX_BYTES = 500_000
UA = 'Mozilla/5.0 (compatible; GlobalOutlookResearch/3.1; verification)'
DATE_KEYS = {'article:published_time', 'datepublished', 'date', 'dc.date',
             'dc.date.issued', 'citation_publication_date', 'citation_date',
             'pubdate', 'publishdate', 'article:modified_time', 'datemodified'}
BAD = re.compile(r'^(skip to|read more|here$|discover more|insights$|podcasts?$|contact|login|sign in|cookie|privacy|about us|subscribe|home$)', re.I)
GOOD = re.compile(r'outlook|investment views?|weekly|monthly|market (updates?|recap|commentary)|asset allocation|global views?|strategy|forecast|perspectives', re.I)

class PageParser(html.parser.HTMLParser):
    def __init__(self):
        super().__init__(); self.dates=[]; self.jsonld=[]; self.in_json=False; self.buf=[]
    def handle_starttag(self, tag, attrs):
        a={k.lower():v for k,v in attrs if k}
        if tag.lower() == 'meta':
            k=(a.get('property') or a.get('name') or a.get('itemprop') or '').lower()
            if k in DATE_KEYS and a.get('content'):
                self.dates.append((k,a['content']))
        if tag.lower() == 'time' and a.get('datetime'):
            self.dates.append(('time.datetime',a['datetime']))
        if tag.lower() == 'script' and 'ld+json' in (a.get('type') or '').lower():
            self.in_json=True; self.buf=[]
    def handle_data(self, data):
        if self.in_json: self.buf.append(data)
    def handle_endtag(self, tag):
        if tag.lower() == 'script' and self.in_json:
            self.jsonld.append(''.join(self.buf)); self.in_json=False

def parse_date(value):
    m=re.search(r'(?<!\d)(20\d{2})[-/](\d{1,2})[-/](\d{1,2})(?!\d)',str(value))
    if not m: return None
    try: return dt.date(*map(int,m.groups()))
    except ValueError: return None

def extract_json_dates(value, out):
    if isinstance(value,list):
        for x in value: extract_json_dates(x,out)
    elif isinstance(value,dict):
        typ=str(value.get('@type','')).lower()
        if isinstance(value.get('@type'),list): typ=' '.join(value['@type']).lower()
        if any(x in typ for x in ('article','report','creativework','news')):
            for key in ('datePublished','dateCreated','dateModified'):
                if value.get(key): out.append(('jsonld.'+key,str(value[key])))
        for x in value.values():
            if isinstance(x,(dict,list)): extract_json_dates(x,out)

def inspect(url, cutoff, today):
    req=urllib.request.Request(url,headers={'User-Agent':UA,'Accept':'text/html,application/pdf;q=0.9,*/*;q=0.5'})
    with urllib.request.urlopen(req,timeout=8) as resp:
        mime=resp.headers.get('Content-Type','').split(';')[0].strip().lower()
        final=resp.geturl(); status=str(resp.status)
        if mime=='application/pdf' or urllib.parse.urlsplit(final).path.lower().endswith('.pdf'):
            return status,final,'pdf','','','pdf_date_requires_review'
        if mime not in ('text/html','application/xhtml+xml'):
            return status,final,mime or 'unknown','','','format_requires_review'
        raw=resp.read(MAX_BYTES)
        parser=PageParser(); parser.feed(raw.decode(resp.headers.get_content_charset() or 'utf-8',errors='replace'))
        evidence=list(parser.dates)
        for blob in parser.jsonld:
            try: extract_json_dates(json.loads(blob),evidence)
            except (ValueError,TypeError): pass
        # Prefer explicit publication fields; never substitute modification date for publication date.
        ranked=[]
        for key,val in evidence:
            d=parse_date(val)
            if d:
                priority=2 if 'modified' in key.lower() else 0 if 'published' in key.lower() or 'publication' in key.lower() or 'issued' in key.lower() else 1
                ranked.append((priority,key,d))
        if not ranked: return status,final,'html','','','date_unverified'
        ranked.sort(key=lambda x:x[0]); priority,key,d=ranked[0]
        if priority==2: result='modification_date_only_requires_review'
        elif cutoff<=d<=today: result='metadata_recent_requires_review'
        else: result='metadata_outside_window_or_future_requires_review'
        return status,final,'html',d.isoformat(),key,result

def main():
    p=argparse.ArgumentParser();p.add_argument('--dir',default='.');p.add_argument('--max-checks',type=int,default=60)
    a=p.parse_args();root=Path(a.dir);today=dt.datetime.now(dt.timezone.utc).date()
    month=today.month-3;year=today.year
    while month<=0: month+=12;year-=1
    cutoff=dt.date(year,month,min(today.day,calendar.monthrange(year,month)[1]))
    with (root/'document_candidates.csv').open(newline='',encoding='utf-8-sig') as f: candidates=list(csv.DictReader(f))
    target=root/'document_verification.csv'; existing={}
    if target.exists():
        with target.open(newline='',encoding='utf-8-sig') as f:
            for row in csv.DictReader(f):
                if row.get('candidate_url'): existing[row['candidate_url']]=row
    fields=['checked_at_utc','source_id','institution_name','candidate_title','candidate_url','final_url','http_status','content_type','metadata_publication_date','date_evidence','review_status','detail']
    unique={}
    for c in candidates:
        url=(c.get('candidate_url') or '').strip()
        if url and urllib.parse.urlsplit(url).scheme in ('http','https') and url not in unique: unique[url]=c
    def rank(item):
        url,c=item;title=c.get('candidate_title','');quality=2 if BAD.search(title.strip()) else 0 if GOOD.search(title+' '+url) else 1
        # Oldest check first to rotate across all candidates rather than repeatedly checking the first 60.
        checked=existing.get(url,{}).get('checked_at_utc','')
        return (quality,checked,url)
    now=dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')
    count=errors=0
    for url,c in sorted(unique.items(),key=rank):
        if count>=max(0,a.max_checks):break
        count+=1;row=dict.fromkeys(fields,'')
        row.update(checked_at_utc=now,source_id=c.get('source_id',''),institution_name=c.get('institution_name',''),candidate_title=c.get('candidate_title',''),candidate_url=url)
        try:
            code,final,kind,date,evidence,status=inspect(url,cutoff,today)
            row.update(final_url=final,http_status=code,content_type=kind,metadata_publication_date=date,date_evidence=evidence,review_status=status)
        except Exception as exc:
            errors+=1;row.update(review_status='fetch_error',detail=f'{type(exc).__name__}: {str(exc)[:150]}')
        existing[url]=row
        print(f'{count}: {row["review_status"]}: {url[:100]}',flush=True)
    with target.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
        for key in sorted(existing):w.writerow({k:existing[key].get(k,'') for k in fields})
    print(f'Checked {count} links; errors {errors}; cumulative archived {len(existing)}. Date window {cutoff} to {today}.',flush=True)
    print('Metadata and HTML time tags are evidence requiring review; no documents or stances certified.',flush=True)

if __name__=='__main__':main()
