"""Offline evidence collector tests; no network requests."""
import csv
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from collect_document_evidence import run, safe_url

class EvidenceTests(unittest.TestCase):
    def test_collect_preserves_unverified_status(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            with (root / "view_review_queue.csv").open("w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=["institution_name", "document_url", "candidate_title", "source_status", "selection_status"])
                w.writeheader()
                w.writerow({"institution_name": "Manager A", "document_url": "https://example.org/outlook", "candidate_title": "Investment outlook", "source_status": "candidate_not_content_verified", "selection_status": "priority_manual_review"})
                w.writerow({"institution_name": "Manager B", "document_url": "https://example.org/banner", "candidate_title": "I agree", "source_status": "candidate_low_quality_metadata"})
            with patch("collect_document_evidence.inspect", return_value=("html_read", "Outlook", "Description", "Equities are discussed.")) as mock:
                run(root, max_checks=12)
                mock.assert_called_once_with("https://example.org/outlook")
            with (root / "document_evidence.csv").open(newline="", encoding="utf-8") as f:
                rows = list(csv.DictReader(f))
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["evidence_status"], "unverified_excerpt_requires_review")
            self.assertEqual(rows[0]["text_excerpt"], "Equities are discussed.")
    def test_rejects_non_https_urls(self):
        self.assertFalse(safe_url("http://example.org"))
        self.assertFalse(safe_url("https://user:pass@example.org"))
        self.assertTrue(safe_url("https://example.org/outlook"))

if __name__ == "__main__":
    unittest.main()
