#!/usr/bin/env python3
import unittest
from build_review_queue import triage_score, PENDING, FINISHED

class QueueTriageTests(unittest.TestCase):
    def test_primary_source_over_aggregator(self):
        primary={"candidate_id":"a", "priority":"P1", "raw_url":"https://assetmanager.com/2026-outlook", "original_title":"Investment Outlook 2026", "review_status":"pending_primary_content"}
        aggregator={**primary,"candidate_id":"b","raw_url":"https://news.google.com/rss/articles/foo"}
        self.assertGreater(triage_score(primary),triage_score(aggregator))
    def test_completed_not_pending(self):
        self.assertNotIn("validated_primary_document",PENDING)
        self.assertIn("validated_primary_document",FINISHED)
    def test_unverified_stays_unverified(self):
        self.assertIn("pending_publication_date",PENDING)

if __name__=="__main__":
    unittest.main()
