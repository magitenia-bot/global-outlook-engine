import unittest
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from ingest_yield_curves import parse_usa,parse_japan
class Parsers(unittest.TestCase):
 def test_usa(self):
  s=("Date,1 Mo,2 Mo,3 Mo,4 Mo,6 Mo,1 Yr,2 Yr,3 Yr,5 Yr,7 Yr,10 Yr,20 Yr,30 Yr\n"
     "11/10/2026,4.05,4.21,4.30,4.28,4.38,4.56,4.73,4.74,4.81,4.89,4.98,5.39,5.35\n")
  data=parse_usa(s.encode(),"official")
  self.assertEqual(next(r["yield_pct"] for r in data if r["maturity_years"]==10),4.98)
 def test_japan(self):
  raw=b"Date,1Y,2Y,3Y,5Y,10Y,20Y,30Y\n2026/11/10,1.597,1.784,1.876,2.124,2.748,3.629,3.935\n"
  data=parse_japan(raw)
  self.assertEqual(next(r["yield_pct"] for r in data if r["maturity_years"]==10),2.748)
 def test_reject_unrecognized(self):
  with self.assertRaises(ValueError):parse_japan(b"Date,unknown\n2026/11/10,1.23\n")
if __name__=="__main__":unittest.main()
