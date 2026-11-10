#!/usr/bin/env python3
"""Public-source discovery only. Never generates investment recommendations."""
import csv, datetime as dt, hashlib, io, json, os, pathlib, re, time
import urllib.error, urllib.parse, urllib.request
import xml.etree.ElementTree as ET
from html.parser import HTMLParser

ROOT=pathlib.Path(__file__).resolve().parent
OUT=ROOT/"research_monitor"
OUT.mkdir(exist_ok=True)
STATE=OUT/"state.json"
EVENTS=OUT/"discovered_documents.csv"
HEADERS=["found_at_utc","manager","source_url","document_url","title","source_type","status","content_hash"]
REGISTRIES=[
 "independent_boutiques_registry_2026-11-11.csv",
 "asia_emerging_traditional_managers_registry_2026-11-10.csv",
 "alternative_managers_registry_2026-11-10.csv",
 "citywire_source_registry_2026-11-11.csv",
 "morningstar_source_registry_2026-11-11.csv",
]
MAX_FETCH=80
MAX_SEARCH=20
UA="GlobalOutlookResearchMonitor/1.0 (public research discovery; contact repository owner)"
class PageTitle(HTMLParser):
 def __init__(self): super().__init__(); self.in_title=False; self.title=[]
 def handle_starttag(self,tag,attrs):
  if tag=="title": self.in_title=True
 def handle_endtag(self,tag):
  if tag=="title": self.in_title=False
 def handle_data(self,data):
  if self.in_title: self.title.append(data)
def request(url):
 if not url.startswith("https://"): raise ValueError("HTTPS only")
 req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"text/html,application/rss+xml,application/xml,application/pdf;q=0.8,*/*;q=0.3"})
 with urllib.request.urlopen(req,timeout=12) as res:
  final=res.geturl()
  if not final.startswith("https://"): raise ValueError("non-HTTPS redirect")
  content_type=res.headers.get("Content-Type","").lower()
  if not any(t in content_type for t in ("text/","xml","pdf")): raise ValueError("unsupported content")
  body=res.read(400_001)
  if len(body)>400_000: raise ValueError("document too large for bounded scan")
  return final,body,content_type
def rows(path):
 if not path.exists(): return []
 with path.open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))
def names_and_sources():
 names=set(); sources=[]
 for filename in REGISTRIES:
  for row in rows(ROOT/filename):
   name=(row.get("manager") or row.get("institution") or "").strip()
   if name: names.add(name)
   url=(row.get("source_url") or "").strip()
   if name and url.startswith("https://"):sources.append((name,url))
 # Add pre-existing official source records
 for filename in ("research_views_2026-11-10_tranche4_20.csv","expanded_official_outlooks.csv"):
  for row in rows(ROOT/filename):
   name=(row.get("institution") or row.get("institution_name") or "").strip()
   if name:names.add(name)
   url=(row.get("source_url") or row.get("document_url") or "").strip()
   if name and url.startswith("https://"):sources.append((name,url))
 return sorted(names),sorted(set(sources))
def append_event(row):
 existing=rows(EVENTS)
 key=(row["manager"],row["document_url"],row["content_hash"])
 if any((r["manager"],r["document_url"],r["content_hash"])==key for r in existing):return False
 with EVENTS.open("a",newline="",encoding="utf-8") as f:
  w=csv.DictWriter(f,fieldnames=HEADERS)
  if not existing:w.writeheader()
  w.writerow(row)
 return True
def main():
 now=dt.datetime.now(dt.timezone.utc)
 mode=os.environ.get("RESEARCH_MODE","hourly")
 state=json.loads(STATE.read_text()) if STATE.exists() else {"hashes":{},"cursor":0,"search_cursor":0}
 names,sources=names_and_sources()
 cursor=int(state.get("cursor",0)); search_cursor=int(state.get("search_cursor",0))
 examined=changed=errors=0
 # Rotate to cover all known URLs over successive hours, without hammering a single domain.
 chosen=[sources[(cursor+i)%len(sources)] for i in range(min(MAX_FETCH,len(sources)))] if sources else []
 state["cursor"]=(cursor+len(chosen))%len(sources) if sources else 0
 for name,url in chosen:
  examined+=1
  try:
   final,body,ctype=request(url)
   digest=hashlib.sha256(body).hexdigest()
   key=hashlib.sha256((name+"|"+url).encode()).hexdigest()
   if state["hashes"].get(key)!=digest:
    title="PDF document" if "pdf" in ctype else ""
    if not title:
     parser=PageTitle();parser.feed(body.decode("utf-8","replace"));title=" ".join(parser.title).strip()[:240]
    if append_event({"found_at_utc":now.isoformat(),"manager":name,"source_url":url,"document_url":final,"title":title,"source_type":"registered_source","status":"requires_human_classification","content_hash":digest}):changed+=1
   state["hashes"][key]=digest
  except Exception as e:
   errors+=1
   print("SOURCE_ERROR",name,url,type(e).__name__,str(e)[:120])
  time.sleep(0.15)
 # Daily discovery uses public news RSS search. A result is only a candidate, never a validated view.
 if mode=="daily" and names:
  selected=[names[(search_cursor+i)%len(names)] for i in range(min(MAX_SEARCH,len(names)))]
  state["search_cursor"]=(search_cursor+len(selected))%len(names)
  for name in selected:
   query=urllib.parse.quote(name+' ("investment outlook" OR "market outlook" OR "asset allocation")')
   url="https://news.google.com/rss/search?q="+query+"&hl=en-US&gl=US&ceid=US:en"
   try:
    _,body,_=request(url)
    root=ET.fromstring(body)
    for item in root.findall("./channel/item")[:5]:
     link=(item.findtext("link") or "").strip()
     title=(item.findtext("title") or "").strip()
     if not link.startswith("https://"):continue
     digest=hashlib.sha256((link+title).encode()).hexdigest()
     if append_event({"found_at_utc":now.isoformat(),"manager":name,"source_url":url,"document_url":link,"title":title[:240],"source_type":"search_candidate","status":"unverified_attribution_and_view","content_hash":digest}):changed+=1
   except Exception as e:
    errors+=1;print("DISCOVERY_ERROR",name,type(e).__name__,str(e)[:120])
   time.sleep(0.15)
 STATE.write_text(json.dumps(state,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
 (OUT/"last_run.json").write_text(json.dumps({"utc":now.isoformat(),"mode":mode,"registered_managers":len(names),"registered_sources":len(sources),"sources_checked":examined,"new_records":changed,"errors":errors,"view_classifications_created":0},indent=2)+"\n")
 print("RESULT",mode,"managers",len(names),"sources",len(sources),"checked",examined,"new",changed,"errors",errors)
if __name__=="__main__":main()
