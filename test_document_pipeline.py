"""Regression tests for document frequency and PDF discovery."""
import csv
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from select_outlooks_v21 import classify
from discover import main as discovery_main
from verify_documents_v2 import parse_date, PageParser

class ClassificationTests(unittest.TestCase):
    def classify_title(self, title):
        return classify({'candidate_title': title, 'candidate_url': 'https://example.org/research/report',
                         'http_status': '200', 'metadata_publication_date': ''},
                        __import__('datetime').date(2026,11,10),
                        __import__('datetime').date(2026,8,10))['frequency_bucket']

    def test_quarterly(self):
        self.assertEqual(self.classify_title('Quarterly market outlook Q4 2026'), 'quarterly')

    def test_strategic(self):
        self.assertEqual(self.classify_title('2026 annual investment outlook'), 'strategic')

    def test_monthly(self):
        self.assertEqual(self.classify_title('Global Investment Views November'), 'monthly')

    def test_weekly(self):
        self.assertEqual(self.classify_title('Weekly market commentary'), 'weekly')

    def test_european_date_parsing(self):
        self.assertEqual(str(parse_date('10/11/2026')), '2026-11-10')
        self.assertEqual(str(parse_date('2026-11-09')), '2026-11-09')

    def test_visible_time_tag(self):
        parser = PageParser()
        parser.feed('<article><time>10/11/2026</time></article>')
        self.assertIn(('time.text', '10/11/2026'), parser.dates)

    def test_direct_pdf_discovery(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            with (root/'sources.csv').open('w',newline='',encoding='utf-8') as f:
                w=csv.DictWriter(f,fieldnames=['source_id','institution_name','source_name','source_url','status','frequency'])
                w.writeheader()
                w.writerow({'source_id':'pdf-1','institution_name':'Example Manager','source_name':'2026 Investment Outlook',
                            'source_url':'https://example.org/outlook.pdf','status':'active','frequency':'weekly'})
            with patch('sys.argv',['discover.py','--dir',d]):
                discovery_main()
            with (root/'document_candidates.csv').open(newline='',encoding='utf-8') as f:
                records=list(csv.DictReader(f))
            self.assertEqual(len(records),1)
            self.assertEqual(records[0]['review_status'],'candidate_pdf_unverified')
            self.assertEqual(records[0]['candidate_url'],'https://example.org/outlook.pdf')

if __name__ == '__main__':
    unittest.main()
