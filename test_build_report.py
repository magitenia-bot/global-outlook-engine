"""Regression checks for conservative consensus and HTML rendering."""
import csv
import json
import tempfile
import unittest
from pathlib import Path

from build_report import render


class DashboardTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def write_views(self, count):
        fields = [
            "institution_name", "document_url", "publication_date",
            "frequency", "asset_class", "stance", "reviewed_at_utc",
            "reviewer", "evidence_quote", "previous_stance", "previous_document_url",
        ]
        with (self.root / "validated_views.csv").open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            for n in range(count):
                writer.writerow({
                    "institution_name": f"Manager {n}",
                    "document_url": f"https://example.org/outlook/{n}",
                    "publication_date": "2026-11-01",
                    "frequency": "monthly",
                    "asset_class": "Equity",
                    "stance": "positive",
                    "reviewed_at_utc": "2026-11-02T12:00:00+00:00",
                    "reviewer": "QA reviewer",
                    "evidence_quote": "Positive equity outlook.",
                })

    def test_no_validated_views_remains_unavailable(self):
        self.write_views(0)
        render(self.root)
        html = (self.root / "global_outlook.html").read_text(encoding="utf-8")
        status = json.loads((self.root / "report_status.json").read_text(encoding="utf-8"))
        self.assertIn("Nessuna view validata", html)
        self.assertEqual(status["validated_view_rows"], 0)

    def test_two_managers_do_not_produce_consensus(self):
        self.write_views(2)
        render(self.root)
        html = (self.root / "global_outlook.html").read_text(encoding="utf-8")
        self.assertIn("n.d. — campione insufficiente", html)
        self.assertEqual(html.count("n.d. — campione insufficiente"), 1)

    def test_three_managers_produce_consensus(self):
        self.write_views(3)
        render(self.root)
        html = (self.root / "global_outlook.html").read_text(encoding="utf-8")
        status = json.loads((self.root / "report_status.json").read_text(encoding="utf-8"))
        self.assertIn('class="tag pos">Positivo</span>', html)
        self.assertNotIn("n.d. — campione insufficiente</span>", html)
        self.assertEqual(status["validated_view_rows"], 3)


if __name__ == "__main__":
    unittest.main()
