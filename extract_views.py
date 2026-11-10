#!/usr/bin/env python3
"""Create a review queue from candidate outlook metadata; never auto-approve a stance.

This intentionally does not claim to have read linked documents. Evidence and
stance must be added by a reviewer after opening the primary source.
"""
import argparse
import csv
import datetime as dt
from pathlib import Path

GENERIC_TITLES = {'i agree', 'accept', 'english', 'italian', 'go deeper', 'more', 'download', 'outlook'}

FIELDS = ['institution_name','document_url','publication_date','frequency','asset_class','proposed_stance','evidence_quote','review_status','source_status','candidate_title','selection_status','checked_at_utc']

def read_csv(path):
    if not path.exists():
        return []
    with path.open(newline='', encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))

def run(root):
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    old = read_csv(root / 'view_review_queue.csv')
    preserved = {(r.get('institution_name',''),r.get('document_url',''),r.get('frequency','')):r for r in old}
    output = {}
    for freq in ('weekly',):
        for r in read_csv(root / f'outlook_{freq}_candidates.csv'):
            url = (r.get('final_url') or r.get('candidate_url') or '').strip()
            name = (r.get('institution_name') or '').strip()
            if not name or not url.startswith('https://'):
                continue
            key = (name,url,freq)
            title = (r.get('candidate_title') or '').strip()
            low_quality = title.casefold() in GENERIC_TITLES or not title
            prior = preserved.get(key, {})
            row = {
                'institution_name':name,
                'document_url':url,
                'publication_date':r.get('metadata_publication_date',''),
                'frequency':freq,
                'asset_class':prior.get('asset_class',''),
                'proposed_stance':prior.get('proposed_stance',''),
                'evidence_quote':prior.get('evidence_quote',''),
                'review_status':prior.get('review_status','pending_source_review'),
                'source_status':('candidate_low_quality_metadata' if low_quality else 'candidate_not_content_verified'),
                'candidate_title':title,
                'selection_status':r.get('selection_status',''),
                'checked_at_utc':r.get('checked_at_utc') or now,
            }
            output[key]=row
    with (root/'view_review_queue.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader();w.writerows(sorted(output.values(),key=lambda x:(x['institution_name'],x['frequency'],x['document_url'])))
    low_quality_count = sum(r.get('source_status') == 'candidate_low_quality_metadata' for r in output.values())
    print(f'View review queue: {len(output)} records ({low_quality_count} low-quality metadata); zero views automatically approved')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--dir',default='.');args=p.parse_args();run(Path(args.dir))
