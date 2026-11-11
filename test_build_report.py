"""Regression checks for conservative consensus and HTML rendering."""
import csv
import datetime as dt
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
                    "publication_date": dt.datetime.now(dt.timezone.utc).date().isoformat(),
                    "frequency": "weekly",
                    "asset_class": "Equity",
                    "stance": "positive",
                    "reviewed_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
                    "reviewer": "QA reviewer",
                    "evidence_quote": "Positive equity outlook.",
                })

    def mark_chatgpt_verified(self):
        path = self.root / "validated_views.csv"
        with path.open(newline="", encoding="utf-8") as f:
            rs = list(csv.DictReader(f))
        for r in rs:
            r["reviewer"] = "ChatGPT - verifica documentale completata"
        with path.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=rs[0].keys())
            w.writeheader()
            w.writerows(rs)

    def write_sources(self, count):
        with (self.root / "sources.csv").open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["institution_name", "source_url", "status"])
            w.writeheader()
            for n in range(count):
                w.writerow({"institution_name": f"Manager {n}", "source_url": "https://example.org/research", "status": "active"})


    def test_direct_research_is_separate_from_consensus(self):
        with (self.root / 'direct_weekly_matrix_2026-11-10.csv').open('w', encoding='utf-8', newline='') as f:
            w = csv.DictWriter(f, fieldnames=['institution','weekly_publication_date','official_url','asset_or_theme','stance','stance_type','traffic_light','change_arrow_status'])
            w.writeheader()
            w.writerow({'institution':'BlackRock','weekly_publication_date':dt.datetime.now(dt.timezone.utc).date().isoformat(),'official_url':'https://www.blackrock.com/weekly','asset_or_theme':'US equities','stance':'neutral','stance_type':'explicit'})
            w.writerow({'institution':'Amundi','weekly_publication_date':dt.datetime.now(dt.timezone.utc).date().isoformat(),'official_url':'https://www.amundi.com/weekly','asset_or_theme':'AI','stance':'diversification_preferred','stance_type':'thematic'})
        render(self.root)
        page = (self.root / 'global_outlook.html').read_text(encoding='utf-8')
        self.assertIn('Ricerca diretta', page)
        self.assertIn('BlackRock', page)
        self.assertIn('Neutrale', page)
        self.assertNotIn('diversification_preferred', page)
        status = json.loads((self.root / 'report_status.json').read_text(encoding='utf-8'))
        self.assertEqual(status['validated_view_rows'], 0)

    def test_registered_source_alone_does_not_validate_a_view(self):
        self.write_views(3)
        with (self.root / "sources.csv").open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["institution_name", "source_url", "status"])
            w.writeheader()
            for n in range(3):
                w.writerow({"institution_name": f"Manager {n}", "source_url": "https://example.org/research", "status": "active"})
        render(self.root)
        status = json.loads((self.root / "report_status.json").read_text(encoding="utf-8"))
        self.assertEqual(status["source_admitted_view_rows"], 0)
        self.assertNotIn("independently_approved_view_rows", status)
        self.assertEqual(status["validated_view_rows"], 0)

    def test_unregistered_domain_still_remains_provisional(self):
        self.write_views(1)
        with (self.root / "sources.csv").open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["institution_name", "source_url", "status"])
            w.writeheader()
            w.writerow({"institution_name": "Manager 0", "source_url": "https://notexample.org/research", "status": "active"})
        render(self.root)
        status = json.loads((self.root / "report_status.json").read_text(encoding="utf-8"))
        self.assertEqual(status["source_admitted_view_rows"], 0)
        self.assertEqual(status["provisional_view_rows"], 1)

    def test_source_registry_renders_release_dates_and_unknowns(self):
        self.write_views(0)
        with (self.root / "outlook_source_registry.csv").open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["institution_name","document_url","publication_date","as_of_date","verification_status"])
            w.writeheader()
            w.writerow({"institution_name":"Manager A","document_url":"https://example.org/outlook","publication_date":"2026-10-21","as_of_date":"2026-09-30","verification_status":"official_page_date_checked"})
            w.writerow({"institution_name":"Manager B","document_url":"https://example.org/other","publication_date":"n.d.","as_of_date":"n.d.","verification_status":"official_source_registered_date_not_verified"})
        render(self.root)
        html = (self.root / "global_outlook.html").read_text(encoding="utf-8")
        status = json.loads((self.root / "report_status.json").read_text(encoding="utf-8"))
        self.assertIn("2026-10-21", html)
        self.assertIn("2026-09-30", html)
        self.assertIn("Manager B", html)
        self.assertEqual(status["registered_source_documents"], 2)
        self.assertEqual(status["sources_with_page_date"], 1)

    def test_missing_manager_coverage_is_explicit(self):
        self.write_views(0)
        with (self.root / "sources.csv").open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["institution_name","source_url","status"])
            w.writeheader()
            w.writerow({"institution_name":"Manager without views","source_url":"https://example.org/outlook","status":"active"})
        render(self.root)
        html = (self.root / "global_outlook.html").read_text(encoding="utf-8")
        status = json.loads((self.root / "report_status.json").read_text(encoding="utf-8"))
        self.assertIn("Manager without views", html)
        self.assertEqual(status["view_coverage_percent"], 0.0)
        self.assertEqual(status["institutions_without_views"], ["Manager without views"])

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

    def test_ai_views_are_visible_but_excluded_from_consensus(self):
        self.write_views(3)
        path = self.root / "validated_views.csv"
        with path.open(newline="", encoding="utf-8") as f:
            records = list(csv.DictReader(f))
        for r in records:
            r["reviewer"] = "ChatGPT - verifica assistita da IA"
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=records[0].keys())
            writer.writeheader()
            writer.writerows(records)
        render(self.root)
        html = (self.root / "global_outlook.html").read_text(encoding="utf-8")
        status = json.loads((self.root / "report_status.json").read_text(encoding="utf-8"))
        self.assertEqual(status["validated_view_rows"], 0)
        self.assertEqual(status["provisional_view_rows"], 3)
        self.assertIn("Matrice esplorativa", html)

    def test_discovery_does_not_exclude_unreachable_or_generic(self):
        import datetime as dt
        from select_outlooks_v21 import classify
        today = dt.date(2026, 11, 11)
        row = {"candidate_title": "Read more", "candidate_url": "https://example.org/contact",
               "http_status": "403", "metadata_publication_date": ""}
        result = classify(row, today, dt.date(2026, 9, 11))
        self.assertIn(result["selection_status"], ("manual_date_review", "manual_unclassified_review"))

    def test_all_frequency_sections_are_present(self):
        self.write_views(0)
        render(self.root)
        html = (self.root / "global_outlook.html").read_text(encoding="utf-8")
        for label in ("Settimanali", "Mensili", "Trimestrali", "Strategici / annuali"):
            self.assertIn(label, html)

    def test_no_validated_views_remains_unavailable(self):
        self.write_views(0)
        render(self.root)
        html = (self.root / "global_outlook.html").read_text(encoding="utf-8")
        status = json.loads((self.root / "report_status.json").read_text(encoding="utf-8"))
        self.assertIn("Nessuna view ammessa", html)
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
        with (self.root / "view_review_queue.csv").open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["document_url", "frequency", "institution_name"])
            w.writeheader()
            w.writerow({"document_url": "https://example.org/outlook", "frequency": "weekly", "institution_name": "Manager A"})
        render(self.root)
        html = (self.root / "global_outlook.html").read_text(encoding="utf-8")
        status = json.loads((self.root / "report_status.json").read_text(encoding="utf-8"))
        self.assertIn("Research text for verification.", html)
        self.assertIn("NON rappresentano view validate", html)
        self.assertEqual(status["readable_evidence_rows"], 1)
        self.assertEqual(status["validated_view_rows"], 0)

    def test_two_managers_do_not_produce_consensus(self):
        self.write_views(2)
        self.mark_chatgpt_verified()
        self.write_sources(2)
        render(self.root)
        html = (self.root / "global_outlook.html").read_text(encoding="utf-8")
        self.assertIn("n.d. — campione insufficiente", html)
        self.assertEqual(html.count("n.d. — campione insufficiente"), 1)

    def test_ai_views_require_registered_official_source(self):
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
        self.assertIn("non contribuiscono ai semafori né al consensus", html)
        self.assertIn("Nessuna view ammessa", html)

    def test_ai_completed_verification_requires_no_human_reviewer(self):\n        self.write_views(1)\n        self.mark_chatgpt_verified()\n        render(self.root)\n        status = json.loads((self.root / 'report_status.json').read_text(encoding='utf-8'))\n        self.assertEqual(status['validated_view_rows'], 1)\n\n    def test_three_managers_produce_consensus(self):
        self.write_views(3)
        self.mark_independent()
        self.write_sources(3)
        render(self.root)
        html = (self.root / "global_outlook.html").read_text(encoding="utf-8")
        status = json.loads((self.root / "report_status.json").read_text(encoding="utf-8"))
        self.assertIn('class="tag pos">Positivo</span>', html)
        self.assertNotIn("n.d. — campione insufficiente</span>", html)
        self.assertEqual(status["validated_view_rows"], 3)


if __name__ == "__main__":
    unittest.main()
