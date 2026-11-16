#!/usr/bin/env python3
"""Regression checks for Global Outlook source coverage; no network requests."""
import csv
import pathlib
import tempfile
import unittest
from unittest.mock import patch
import research_monitor as mon


class SourceCoverage(unittest.TestCase):
 def test_registry_and_catalog_merged_without_double_counting(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=pathlib.Path(tmp)
   with (root/"sources.csv").open("w",newline="",encoding="utf-8") as fh:
    w=csv.DictWriter(fh,fieldnames=["institution_name","source_url","priority","status"])
    w.writeheader()
    w.writerows([
     {"institution_name":"Major A","source_url":"https://example.com/a","priority":"1","status":"active"},
     {"institution_name":"Major B","source_url":"https://example.com/b","priority":"2","status":"active"},
     {"institution_name":"Excluded","source_url":"https://example.com/c","priority":"1","status":"disabled"},
     {"institution_name":"Nonsecure","source_url":"http://example.com/d","priority":"1","status":"active"}])
   with (root/"legacy.csv").open("w",newline="",encoding="utf-8") as fh:
    w=csv.DictWriter(fh,fieldnames=["manager","source_url"])
    w.writeheader()
    w.writerow({"manager":"Major A","source_url":"https://example.com/a"})
   with patch.object(mon,"ROOT",root),patch.object(mon,"REGISTRIES",["legacy.csv"]):
    names,sources=mon.names_and_sources()
   self.assertEqual(len(sources),2)
   self.assertEqual(sources[0],(1,"Major A","https://example.com/a"))
   self.assertEqual(sources[1],(2,"Major B","https://example.com/b"))
   self.assertIn("Excluded",names)
   self.assertNotIn("https://example.com/c",str(sources))
   self.assertNotIn("http://example.com/d",str(sources))


if __name__=="__main__":
 unittest.main()
