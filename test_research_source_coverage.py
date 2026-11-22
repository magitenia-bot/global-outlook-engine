#!/usr/bin/env python3
"""Regression checks for the approved Global Outlook source scope; no network."""
import csv
import json
import pathlib
import tempfile
import unittest
from unittest.mock import patch
import research_monitor as mon


class SourceCoverage(unittest.TestCase):
 def test_approved_catalog_aliases_and_duplicates(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=pathlib.Path(tmp)
   contract=root/"research_curated/global_outlook_contract.json"
   contract.parent.mkdir()
   contract.write_text(json.dumps({"research_scope":{
    "managers":["Major A","Major B","Excluded","Nonsecure"],
    "aliases":{"Major A alias":"Major A"}
   }}),encoding="utf-8")
   with (root/"sources.csv").open("w",newline="",encoding="utf-8") as fh:
    w=csv.DictWriter(fh,fieldnames=["institution_name","source_url","priority","status"])
    w.writeheader()
    w.writerows([
     {"institution_name":"Major A","source_url":"https://example.com/a","priority":"2","status":"active"},
     {"institution_name":"Major A alias","source_url":"https://example.com/a","priority":"1","status":"verified"},
     {"institution_name":"Major B","source_url":"https://example.com/b","priority":"2","status":"active"},
     {"institution_name":"Excluded","source_url":"https://example.com/c","priority":"1","status":"disabled"},
     {"institution_name":"Nonsecure","source_url":"http://example.com/d","priority":"1","status":"active"},
     {"institution_name":"Outside scope","source_url":"https://example.com/e","priority":"1","status":"active"}])
   with (root/"legacy.csv").open("w",newline="",encoding="utf-8") as fh:
    w=csv.DictWriter(fh,fieldnames=["manager","source_url"])
    w.writeheader()
    w.writerow({"manager":"Outside scope","source_url":"https://example.com/legacy"})
   with patch.object(mon,"ROOT",root),patch.object(mon,"REGISTRIES",["legacy.csv"]):
    names,sources=mon.names_and_sources()
   self.assertEqual(names,["Excluded","Major A","Major B","Nonsecure"])
   self.assertEqual(sources,[
    (1,"Major A","https://example.com/a"),
    (2,"Major B","https://example.com/b")])

 def test_missing_contract_fails_closed(self):
  with tempfile.TemporaryDirectory() as tmp:
   with patch.object(mon,"ROOT",pathlib.Path(tmp)):
    with self.assertRaises(FileNotFoundError):
     mon.names_and_sources()


if __name__=="__main__":
 unittest.main()
