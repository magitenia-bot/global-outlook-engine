#!/usr/bin/env python3
"""Regression checks for Global Outlook validation; uses temporary directories."""
import csv, pathlib, subprocess, sys, tempfile
SCRIPT=pathlib.Path(__file__).with_name("validate_candidate.py")
def run(folder,id,result,reason="",extra=None):
    cmd=[sys.executable,str(SCRIPT),"--dir",str(folder),"--candidate-id",id,"--manager","Test Manager","--document-url","https://example.org/primary","--result",result,"--reason",reason]
    if extra: cmd+=extra
    return subprocess.run(cmd,capture_output=True,text=True)
with tempfile.TemporaryDirectory() as tmp:
    d=pathlib.Path(tmp)
    assert run(d,"A","fail","source inaccessible").returncode==0
    assert run(d,"A","fail","date not verified").returncode==0
    assert run(d,"A","pass",extra=["--source-kind","official_primary","--document-date","2026-11-18","--asset-class","Azionario USA","--stance","overweight","--evidence","documented"]).returncode!=0
    with (d/"candidate_exclusions.csv").open() as f: assert len(list(csv.DictReader(f)))==1
    assert run(d,"B","pass",extra=["--source-kind","official_primary","--document-date","2026-11-18","--asset-class","Azionario USA","--stance","overweight","--evidence","documented"]).returncode==0
    assert run(d,"B","fail","later attempt").returncode!=0
    assert run(d,"C","pass",extra=["--source-kind","official_primary"]).returncode!=0
    assert not any(r["candidate_id"]=="C" for r in csv.DictReader((d/"candidate_validation_ledger.csv").open()))
print("PASS: 2 attempts/exclusion, approved immutability, incomplete evidence rejection")
