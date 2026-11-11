#!/usr/bin/env python3
"""Raccoglie serie primarie per le curve. In caso di errore conserva lo storico."""
import csv, io, json, re, urllib.request
from datetime import date, datetime, timezone
from pathlib import Path

BASE=Path(__file__).resolve().parent/"data"
FILE=BASE/"yield_curves.csv"
STATUS=BASE/"ingestion_status.json"
FIELDS=["date","country","curve_type","maturity_years","yield_pct","source_url","verification_note"]
US_COLS={"1 Mo":1/12,"1.5 Mo":1.5/12,"2 Mo":2/12,"3 Mo":.25,"4 Mo":1/3,"6 Mo":.5,"1 Yr":1,"2 Yr":2,"3 Yr":3,"5 Yr":5,"7 Yr":7,"10 Yr":10,"20 Yr":20,"30 Yr":30}
US_BASE="https://home.treasury.gov/resource-center/data-chart-center/interest-rates/daily-treasury-rates.csv/{year}/all?type=daily_treasury_yield_curve&field_tdr_date_value={year}&page&_format=csv"
JP_URL="https://www.mof.go.jp/jgbs/reference/interest_rate/jgbcm.csv"

def download(url):
    req=urllib.request.Request(url,headers={"User-Agent":"GlobalMacroCycle-SourceMonitor/1.0"})
    with urllib.request.urlopen(req,timeout=25) as r:
        value=r.read(9_000_001)
    if not value or len(value)>9_000_000: raise ValueError("Risposta vuota o troppo lunga")
    return value

def parse_date(s):
    for f in ("%m/%d/%Y","%Y/%m/%d","%Y-%m-%d"):
        try:return datetime.strptime(str(s).strip(),f).date().isoformat()
        except ValueError:pass
    return None

def parse_num(s):
    try:
        n=float(str(s).strip().replace("−","-"))
        return n if -5<n<30 else None
    except (ValueError,TypeError): return None

def row(date_,country,type_,tenor,value,url,note):
    return dict(date=date_,country=country,curve_type=type_,maturity_years=round(tenor,4),yield_pct=value,source_url=url,verification_note=note)

def parse_usa(blob,source):
    out=[]
    for values in csv.DictReader(io.StringIO(blob.decode("utf-8-sig"))):
        d=parse_date(values.get("Date"))
        if not d or d>date.today().isoformat(): continue
        pts=[(t,parse_num(values.get(col))) for col,t in US_COLS.items()]
        pts=[(t,v) for t,v in pts if v is not None]
        if len(pts)<8:continue
        out.extend(row(d,"USA","par_constant_maturity",t,v,source,"Official US Treasury daily CMT par curve") for t,v in pts)
    if not out:raise ValueError("Nessuna curva USA valida")
    return out

def parse_japan(blob):
    decoded=None
    for encoding in ("utf-8-sig","cp932","shift_jis"):
        try:decoded=blob.decode(encoding);break
        except UnicodeError:continue
    if decoded is None:raise ValueError("Codifica MOF non leggibile")
    allrows=list(csv.reader(io.StringIO(decoded)))
    header=None
    for i,r in enumerate(allrows[:60]):
        mapping={}
        for j,v in enumerate(r):
            m=re.fullmatch(r"(\d+)\s*(?:Y|Yr|Year|Years)",v.strip(),re.I)
            if m:maturity=int(m.group(1));mapping[j]=maturity
        if {2,5,10}.issubset(mapping.values()):header=(i,mapping);break
    if header is None:raise ValueError("Schema MOF non riconosciuto; storico mantenuto")
    start,mapping=header
    out=[]
    for r in allrows[start+1:]:
        if not r:continue
        d=parse_date(r[0])
        if not d or d>date.today().isoformat():continue
        pts=[(t,parse_num(r[j])) for j,t in mapping.items() if j<len(r)]
        pts=[(t,v) for t,v in pts if v is not None]
        if len(pts)<5:continue
        out.extend(row(d,"JPN","constant_maturity_reference",t,v,JP_URL,"Official Japan MOF reference JGB yields") for t,v in pts)
    if not out:raise ValueError("Nessuna curva JGB valida; storico mantenuto")
    return out

def run():
    BASE.mkdir(exist_ok=True)
    stored={}
    if FILE.exists():
        with FILE.open(encoding="utf-8",newline="") as f:
            for r in csv.DictReader(f):
                try:stored[(r["date"],r["country"],round(float(r["maturity_years"]),4))]=r
                except (KeyError,ValueError):continue
    sources=[
      ("USA",lambda:parse_usa(download(US_BASE.format(year=date.today().year)),US_BASE.format(year=date.today().year))),
      ("JPN",lambda:parse_japan(download(JP_URL)))
    ]
    log=[]
    for name,func in sources:
        try:
            fresh=func()
            for r in fresh:stored[(r["date"],r["country"],round(float(r["maturity_years"]),4))]=r
            log.append({"source":name,"status":"ok","observations":len(fresh),"latest_date":max(r["date"] for r in fresh)})
        except Exception as e:
            log.append({"source":name,"status":"failed_preserved","reason":str(e)[:180]})
    if stored:
        temp=FILE.with_suffix(".tmp")
        with temp.open("w",encoding="utf-8",newline="") as f:
            w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader()
            for r in sorted(stored.values(),key=lambda x:(x["date"],x["country"],float(x["maturity_years"]))):w.writerow(r)
        temp.replace(FILE)
    info={"checked_at_utc":datetime.now(timezone.utc).isoformat(),"events":log,"total_rows":len(stored),"report_generated":False}
    STATUS.write_text(json.dumps(info,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps(info,ensure_ascii=False))
    if not any(entry["status"]=="ok" for entry in log):raise SystemExit(1)

if __name__=="__main__":run()
