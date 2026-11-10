"""Offline regression tests for conservative PDF and topic extraction."""
import csv
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from analyze_evidence import evidence_rows,run
from collect_document_evidence import run as collect

class DocumentContentTests(unittest.TestCase):
    def test_topic_excerpts_never_create_stance(self):
        source={"institution_name":"Manager A","document_url":"https://example.org/report.pdf",
                "fetch_status":"pdf_read","text_excerpt":"Global investment commentary. We discuss equity market valuations and several possible scenarios for the coming year."}
        rows=evidence_rows(source)
        self.assertTrue(any(r["asset_class"]=="Equity" for r in rows))
        self.assertTrue(all(not r["proposed_stance"] for r in rows))
        self.assertTrue(all(r["review_status"]=="pending_human_interpretation" for r in rows))

    def test_missing_text_produces_no_evidence(self):
        self.assertEqual(evidence_rows({"fetch_status":"pdf_no_extractable_text","text_excerpt":""}),[])

    def test_pdf_candidate_is_collected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            with (root/"view_review_queue.csv").open("w",newline="",encoding="utf-8") as f:
                w=csv.DictWriter(f,fieldnames=["institution_name","document_url","candidate_title","source_status"])
                w.writeheader()
                w.writerow({"institution_name":"Manager A","document_url":"https://example.org/report.pdf","candidate_title":"Annual outlook","source_status":"candidate_not_content_verified"})
            with patch("collect_document_evidence.extract_pdf",return_value=("pdf_read","","","Equity markets are discussed in the 2026 annual outlook.")) as mocked:
                collect(root,max_checks=1)
                mocked.assert_called_once_with("https://example.org/report.pdf")
            run(root)
            with (root/"document_topic_evidence.csv").open(newline="",encoding="utf-8") as f:
                rows=list(csv.DictReader(f))
            self.assertTrue(rows)
            self.assertTrue(all(not r["proposed_stance"] for r in rows))

if __name__=="__main__":
    unittest.main()
