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

    def write_approvals(self, count):
        with (self.root / "view_approvals.csv").open("w", newline="", encoding="utf-8") as f:
            fields = ["institution_name", "document_url", "publication_date", "frequency",
                      "asset_class", "stance", "approval_status", "independent_reviewer",
                      "evidence_checked", "reviewed_at_utc", "review_notes"]
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            for n in range(count):
                w.writerow({"institution_name": f"Manager {n}",
                            "document_url": f"https://example.org/outlook/{n}",
                            "publication_date": "2026-11-01", "frequency": "monthly",
                            "asset_class": "Equity", "stance": "positive",
                            "approval_status": "approved", "independent_reviewer": "Independent QA",
                            "evidence_checked": "yes", "reviewed_at_utc": "2026-11-02T13:00:00+00:00"})

    def test_unapproved_non_ai_reviewer_is_not_validation(self):
        self.write_views(3)
        render(self.root)
        status = json.loads((self.root / "report_status.json").read_text(encoding="utf-8"))
        self.assertEqual(status["validated_view_rows"], 0)
        self.assertEqual(status["provisional_view_rows"], 3)

    def test_preliminary_semaphores_visible_without_claiming_validation(self):
        self.write_views(2)
        render(self.root)
        html = (self.root / "global_outlook.html").read_text(encoding="utf-8")
        status = json.loads((self.root / "report_status.json").read_text(encoding="utf-8"))
        self.assertIn("Matrice esplorativa", html)
        self.assertIn("Positivo (preliminare)", html)
        self.assertIn("NON verificati", html)
        self.assertEqual(status["preliminary_traffic_light_rows"], 2)
        self.assertEqual(status["validated_view_rows"], 0)

    def test_no_validated_views_remains_unavailable(self):
        self.write_views(0)
        render(self.root)
        html = (self.root / "global_outlook.html").read_text(encoding="utf-8")
        status = json.loads((self.root / "report_status.json").read_text(encoding="utf-8"))
        self.assertIn("Nessuna view validata", html)
        self.assertEqual(status["validated_view_rows"], 0)

    def test_unverified_excerpts_are_visible_but_not_validated(self):
        self.write_views(0)
        fields = ["institution_name", "document_url", "candidate_title", "publication_date",
                  "checked_at_utc", "fetch_status", "page_title", "page_description",
                  "text_excerpt", "evidence_status"]
        with (self.root / "document_evidence.csv").open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            w.writerow({"institution_name": "Manager A", "document_url": "https://example.org/outlook",
                        "fetch_status": "html_read", "page_title": "Investment outlook",
                        "text_excerpt": "Research text for verification."})
        render(self.root)
        html = (self.root / "global_outlook.html").read_text(encoding="utf-8")
        status = json.loads((self.root / "report_status.json").read_text(encoding="utf-8"))
        self.assertIn("Research text for verification.", html)
        self.assertIn("NON rappresentano view validate", html)
        self.assertEqual(status["readable_evidence_rows"], 1)
        self.assertEqual(status["validated_view_rows"], 0)

    def test_two_managers_do_not_produce_consensus(self):
        self.write_views(2)
        self.write_approvals(2)
        render(self.root)
        html = (self.root / "global_outlook.html").read_text(encoding="utf-8")
        self.assertIn("n.d. — campione insufficiente", html)
        self.assertEqual(html.count("n.d. — campione insufficiente"), 1)

    def test_ai_provisional_views_never_enter_consensus(self):
        self.write_views(3)
        path = self.root / "validated_views.csv"
        with path.open(newline="", encoding="utf-8") as f:
            rs = list(csv.DictReader(f))
        for r in rs:
            r["reviewer"] = "ChatGPT - verifica assistita da IA, non revisione umana"
        with path.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=rs[0].keys())
            w.writeheader()
            w.writerows(rs)
        render(self.root)
        status = json.loads((self.root / "report_status.json").read_text(encoding="utf-8"))
        html = (self.root / "global_outlook.html").read_text(encoding="utf-8")
        self.assertEqual(status["validated_view_rows"], 0)
        self.assertEqual(status["provisional_view_rows"], 3)
        self.assertIn("in attesa di conferma indipendente", html)
        self.assertIn("Nessuna view validata", html)

    def test_three_managers_produce_consensus(self):
        self.write_views(3)
        self.write_approvals(3)
        render(self.root)
        html = (self.root / "global_outlook.html").read_text(encoding="utf-8")
        status = json.loads((self.root / "report_status.json").read_text(encoding="utf-8"))
        self.assertIn('class="tag pos">Positivo</span>', html)
        self.assertNotIn("n.d. — campione insufficiente</span>", html)
        self.assertEqual(status["validated_view_rows"], 3)


if __name__ == "__main__":
    unittest.main()
