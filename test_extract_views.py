"""Tests for outlook candidate review queue quality flags."""
import csv
import tempfile
import unittest
from pathlib import Path
from extract_views import run


class QueueTests(unittest.TestCase):
    def test_generic_titles_flagged_without_approving_views(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            with (root / "outlook_weekly_candidates.csv").open("w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=["institution_name", "candidate_url", "candidate_title"])
                writer.writeheader()
                writer.writerow({"institution_name": "Manager A", "candidate_url": "https://example.org/a", "candidate_title": "I agree"})
                writer.writerow({"institution_name": "Manager B", "candidate_url": "https://example.org/b", "candidate_title": "2026 investment outlook"})
            run(root)
            with (root / "view_review_queue.csv").open(newline="", encoding="utf-8") as f:
                rows = {r["institution_name"]: r for r in csv.DictReader(f)}
            self.assertEqual(rows["Manager A"]["source_status"], "candidate_low_quality_metadata")
            self.assertEqual(rows["Manager B"]["source_status"], "candidate_not_content_verified")
            self.assertTrue(all(r["review_status"] == "pending_source_review" for r in rows.values()))
            self.assertTrue(all(not r["proposed_stance"] for r in rows.values()))


if __name__ == "__main__":
    unittest.main()
