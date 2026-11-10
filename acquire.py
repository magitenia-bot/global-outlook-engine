#!/usr/bin/env python3
"""Monitor official research pages. Detection != document verification.
Usage: python acquire.py --dir "/path/to/Global Outlook 3.0"
Python 3.10+, standard library only. Run on a persistent scheduler with network access.
"""
import argparse,csv,datetime as dt,hashlib,html,json,pathlib,re,time,urllib.request,urllib.error
from html.parser import HTMLParser

class Extract(HTMLParser):
 def __init__(self): super().__init__();self.skip=0;self.words=[];self.links=[];self.href=None
 def handle_starttag(self,t,a):
  if t in ('script','style','noscript'):self.skip+=1
  if t=='a':self.href=dict(a).get('href')
 def handle_endtag(self,t):
  if t in ('script','style','noscript'):self.skip=max(0,self.skip-1)
  if t=='a':self.href=None
 def handle_data(self,s):
  if not self.skip and s.strip():
   self.words.append(s.strip())
   if self.href:self.links.append((s.strip(),self.href))

def read_csv(p):
 with p.open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def write_csv(p,rows,fields):
 temp=p.with_suffix('.tmp')
 with temp.open('w',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(rows)
 temp.replace(p)

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--dir',default='.');ap.add_argument('--timeout',type=int,default=18);a=ap.parse_args()
 root=pathlib.Path(a.dir);root.mkdir(parents=True,exist_ok=True)
 sources=root/'sources.csv';events=root/'acquisition_events.csv'
 src=read_csv(sources);history=read_csv(events) if events.exists() else []
 now=dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')
 for s in src:
  if s['status']!='active':continue
  previous=s.get('last_content_hash','')
  event={'checked_at_utc':now,'source_id':s['source_id'],'institution_id':s['institution_id'],'result':'','http_status':'','content_hash':'','candidate_links_json':'[]','error':''}
  try:
   req=urllib.request.Request(s['source_url'],headers={'User-Agent':'GlobalOutlookResearchMonitor/1.0 (document discovery; contact via source website)','Accept':'text/html,application/xhtml+xml'})
   with urllib.request.urlopen(req,timeout=a.timeout) as resp:
    event['http_status']=str(resp.status);raw=resp.read(2_000_000)
    typ=resp.headers.get('Content-Type','')
   if 'pdf' in typ.lower() or s['source_url'].lower().split('?')[0].endswith('.pdf'):
    digest=hashlib.sha256(raw).hexdigest();event['content_hash']=digest
    event['result']='changed_requires_review' if previous and previous!=digest else ('unchanged' if previous else 'baseline_requires_review')
    event['candidate_links_json']=json.dumps([{'text':s.get('source_name','Official PDF'),'href':s['source_url']}],ensure_ascii=False)
    s['last_content_hash']=digest;s['last_success_at_utc']=now;s['last_result']=event['result']
    s['last_checked_at_utc']=now;history.append(event)
    print(s['source_id'],event['result'],'(PDF source)')
    time.sleep(1)
    continue
   if 'html' not in typ.lower():raise ValueError('Unexpected content type: '+typ)
   parser=Extract();parser.feed(raw.decode('utf-8',errors='replace'))
   normalized=re.sub(r'\s+',' ',' '.join(parser.words)).strip()
   digest=hashlib.sha256(normalized.encode()).hexdigest();event['content_hash']=digest
   event['result']='changed_requires_review' if previous and previous!=digest else ('unchanged' if previous else 'baseline_requires_review')
   links=[{'text':t[:120],'href':u} for t,u in parser.links if re.search(r'outlook|weekly|monthly|commentary|investment views|pdf',t+' '+u,re.I)]
   event['candidate_links_json']=json.dumps(links[:40],ensure_ascii=False)
   s['last_content_hash']=digest;s['last_success_at_utc']=now;s['last_result']=event['result']
  except Exception as e:
   event['result']='error';event['error']=str(e)[:300];s['last_result']='error'
  s['last_checked_at_utc']=now;history.append(event)
  print(s['source_id'],event['result'])
  time.sleep(1)
 write_csv(sources,src,list(src[0]) if src else [])
 fields=['checked_at_utc','source_id','institution_id','result','http_status','content_hash','candidate_links_json','error']
 write_csv(events,history,fields)
 print('IMPORTANT: page changes are discovery signals, not verified documents or stances.')
if __name__=='__main__':main()
