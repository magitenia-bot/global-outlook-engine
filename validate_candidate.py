#!/usr/bin/env python3
"""Global Outlook candidate validation ledger. Standard library only.

No automatic inference of stance or deletion of approved historical views.
Each attempt must be supplied with explicit evidence by an analyst or trusted extractor.
"""
import argparse, csv, datetime as dt, hashlib, json
from pathlib import Path

COLUMNS = ["candidate_id","manager","document_url","document_date","asset_class","stance","evidence","source_kind","checked_at_utc","attempt","result","reason"]
ALLOWED = {"strong_overweight","overweight","neutral","underweight","strong_underweight","positive","negative","n.d."}
def read_csv(path):
    if not path.exists(): return []
    with path.open(encoding="utf-8-sig",newline="") as f: return list(csv.DictReader(f))
def write_csv(path,fields,rows):
    tmp=path.with_suffix(".tmp")
    with tmp.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore");w.writeheader();w.writerows(rows)
    tmp.replace(path)
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--dir",default="research_curated")
    p.add_argument("--candidate-id",required=True)
    p.add_argument("--manager",required=True)
    p.add_argument("--document-url",required=True)
    p.add_argument("--document-date",default="")
    p.add_argument("--asset-class",default="")
    p.add_argument("--stance",default="n.d.")
    p.add_argument("--evidence",default="")
    p.add_argument("--source-kind",choices=["official_primary","other","unavailable"],default="unavailable")
    p.add_argument("--result",choices=["pass","fail"],required=True)
    p.add_argument("--reason",default="")
    a=p.parse_args();root=Path(a.dir);root.mkdir(parents=True,exist_ok=True)
    ledger=root/"candidate_validation_ledger.csv";excluded=root/"candidate_exclusions.csv";approved=root/"candidate_approved.csv"
    rows=read_csv(ledger);id=a.candidate_id.strip()
    if not id: raise SystemExit("candidate ID required")
    past=[r for r in rows if r["candidate_id"]==id]
    if any(r["result"]=="pass" for r in past): raise SystemExit("already approved: immutable")
    if len(past)>=2: raise SystemExit("two attempts exhausted: candidate permanently excluded")
    if past and (past[0]["manager"]!=a.manager or past[0]["document_url"]!=a.document_url): raise SystemExit("candidate identity mismatch")
    valid=a.source_kind=="official_primary" and a.document_url.startswith("https://") and bool(a.document_date) and bool(a.asset_class) and bool(a.evidence.strip()) and a.stance in ALLOWED and a.stance!="n.d."
    if a.result=="pass" and not valid: raise SystemExit("cannot approve without complete primary evidence, asset class and stance")
    if a.result=="fail" and not a.reason.strip(): raise SystemExit("failed attempt requires reason")
    row=dict(candidate_id=id,manager=a.manager,document_url=a.document_url,document_date=a.document_date,asset_class=a.asset_class,stance=a.stance,evidence=a.evidence,source_kind=a.source_kind,checked_at_utc=dt.datetime.now(dt.timezone.utc).isoformat(),attempt=str(len(past)+1),result=a.result,reason=a.reason)
    rows.append(row);write_csv(ledger,COLUMNS,rows)
    if a.result=="pass": write_csv(approved,COLUMNS,read_csv(approved)+[row]);status="approved"
    elif len(past)==1: write_csv(excluded,COLUMNS,read_csv(excluded)+[row]);status="excluded_after_two_attempts"
    else: status="retry_once"
    print(json.dumps({"candidate_id":id,"attempt":len(past)+1,"status":status}))
if __name__=="__main__": main()
