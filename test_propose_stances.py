"""Offline safeguards for unapproved stance proposals."""
import csv
import tempfile
import unittest
from pathlib import Path
from propose_stances import infer,run

class StanceProposalTests(unittest.TestCase):
    def test_explicit_direction_is_weak_hypothesis(self):
        stance,score,_,_=infer({"evidence_excerpt":"We are overweight equities given valuations."})
        self.assertEqual((stance,score),("positive","30"))

    def test_negation_is_not_positive(self):
        stance,score,_,_=infer({"evidence_excerpt":"We are not overweight equities at this time."})
        self.assertEqual((stance,score),("","0"))

    def test_mixed_language_is_not_resolved(self):
        stance,score,_,_=infer({"evidence_excerpt":"We are overweight but cautious on equities."})
        self.assertEqual((stance,score),("","0"))

    def test_conflicting_documents_are_flagged(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            with (root/"document_topic_evidence.csv").open("w",newline="",encoding="utf-8") as f:
                fields=["institution_name","document_url","asset_class","evidence_excerpt"]
                w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
                w.writerow(dict(institution_name="Manager A",document_url="https://example.org/a",asset_class="Equity",evidence_excerpt="We are overweight equities."))
                w.writerow(dict(institution_name="Manager A",document_url="https://example.org/b",asset_class="Equity",evidence_excerpt="We are underweight equities."))
            run(root)
            with (root/"stance_proposals.csv").open(newline="",encoding="utf-8") as f:
                rows=list(csv.DictReader(f))
            self.assertEqual(len(rows),2)
            self.assertTrue(all(r["conflict_status"]=="conflicting_documents" for r in rows))
            self.assertTrue(all(r["confidence_score"]=="0" for r in rows))
            self.assertTrue(all(r["review_status"]=="manual_conflict_resolution_required" for r in rows))

if __name__=="__main__":
    unittest.main()
