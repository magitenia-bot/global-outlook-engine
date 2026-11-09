#!/usr/bin/env python3
"""Global Outlook 3.1 - cautious candidate link checks, stdlib only.
Does not certify publication dates, documents, or investment views.
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

MAX_CHECKS = 60
MAX_BYTES = 350_000
USER_AGENT = 'Mozilla/5.0 (compatible; GlobalOutlookResearch/3.1; document verification)'

class MetaParser(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.dates=[]
    def handle_starttag(self, tag, attrs):
        if tag.lower() != 'meta': return
        a=dict(attrs)
        key=(a.get('property') or a.get('name') or '').lower()
        if key in {'article:published_time','datepublished','date','dc.date','dc.date.issued','citation_publication_date','citation_date'}:
            value=(a.get('content') or '').strip()
            if value: self.dates.append((key,value[:90]))

def get_date(value):
    m=re.search(r'\b(20\d{2})-(\d{2})-(\d{2})\b',value)
    if not m: return None
    try: return dt.date(*map(int,m.groups()))
    except ValueError: return None

def inspect(url, cutoff, today):
    req=urllib.request.Request(url,headers={'User-Agent':USER_AGENT,'Accept':'text/html,application/pdf;q=0.9,*/*;q=0.5'})
    with urllib.request.urlopen(req,timeout=8) as resp:
        mime=resp.headers.get('Content-Type','').split(';')[0].lower().strip()
        final=resp.geturl()
        code=resp.status
        if mime == 'application/pdf' or urllib.parse.urlsplit(final).path.lower().endswith('.pdf'):
            return code,final,'pdf','','','date_unverified'
        if mime not in ('text/html','application/xhtml+xml'):
            return code,final,mime or 'unknown','','','format_requires_review'
        raw=resp.read(MAX_BYTES)
        parser=MetaParser()
        parser.feed(raw.decode(resp.headers.get_content_charset() or 'utf-8',errors='replace'))
        valid=[(k,v,get_date(v)) for k,v in parser.dates if get_date(v)]
        if not valid: return code,final,'html','','','date_unverified'
        k,v,d=valid[0]
        status='metadata_recent_requires_review' if cutoff <= d <= today else 'metadata_outside_window_or_future_requires_review'
        return code,final,'html',d.isoformat(),k,status

def main():
    p=argparse.ArgumentParser();p.add_argument('--dir',default='.');p.add_argument('--max-checks',type=int,default=MAX_CHECKS)
    args=p.parse_args();root=Path(args.dir)
    today=dt.datetime.now(dt.timezone.utc).date()
    month=today.month-3;year=today.year
    while month<=0: month+=12;year-=1
    import calendar
    cutoff=dt.date(year,month,min(today.day,calendar.monthrange(year,month)[1]))
    with (root/'document_candidates.csv').open(newline='',encoding='utf-8-sig') as f: candidates=list(csv.DictReader(f))
    existing={}
    target=root/'document_verification.csv'
    if target.exists():
        with target.open(newline='',encoding='utf-8-sig') as f:
            for row in csv.DictReader(f): existing[row.get('candidate_url','')]=row
    now=dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')
    fields=['checked_at_utc','source_id','institution_name','candidate_title','candidate_url','final_url','http_status','content_type','metadata_publication_date','date_evidence','review_status','detail']
    seen=set();count=0;errors=0
    for c in candidates:
        url=(c.get('candidate_url') or '').strip()
        if not url or url in seen or urllib.parse.urlsplit(url).scheme not in ('http','https'):continue
        seen.add(url)
        if count>=max(0,args.max_checks):break
        count+=1
        row=dict.fromkeys(fields,'')
        row.update(checked_at_utc=now,source_id=c.get('source_id',''),institution_name=c.get('institution_name',''),candidate_title=c.get('candidate_title',''),candidate_url=url)
        try:
            code,final,kind,date,evidence,status=inspect(url,cutoff,today)
            row.update(final_url=final,http_status=str(code),content_type=kind,metadata_publication_date=date,date_evidence=evidence,review_status=status)
        except Exception as exc:
            errors+=1
            row.update(review_status='fetch_error',detail=f'{type(exc).__name__}: {str(exc)[:150]}')
        existing[url]=row
        print(f'{count}/{min(args.max_checks,len(candidates))} {row["review_status"]}: {url[:100]}',flush=True)
    with target.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
        for key in sorted(existing):w.writerow({k:existing[key].get(k,'') for k in fields})
    print(f'Checked {count} candidate URLs; {errors} fetch errors; {len(existing)} cumulative unique URLs in archive.',flush=True)
    print(f'Metadata date window: {cutoff} to {today} (UTC). Dates are UNVERIFIED until source document review.',flush=True)
    print('No documents or investment stances have been certified.',flush=True)

if __name__=='__main__':main()
