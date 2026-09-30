from __future__ import annotations

from batch001_support import OperatorCase

from bie.product_app_v1.stage_timeline import StageTimelineService


class AppRun005Tests(OperatorCase):
    def test_timeline_contains_operator_and_canonical_events(self):
        result = self.imported("timeline")
        view = StageTimelineService(self.context).timeline(result["run"]["run_id"])
        origins = {e["origin"] for e in view["events"]}
        self.assertIn("operator", origins)
        self.assertIn("canonical_persistence", origins)
        self.assertIn("canonical_queue", origins)

    def test_timeline_has_no_fake_progress(self):
        result = self.imported("timeline-progress")
        view = StageTimelineService(self.context).timeline(result["run"]["run_id"])
        self.assertIsNone(view["progress_percent"])
        self.assertFalse(view["fabricated_events"])

    def test_timeline_is_stably_ordered(self):
        result = self.imported("timeline-order")
        events = StageTimelineService(self.context).timeline(result["run"]["run_id"])["events"]
        keys = [(float(e["timestamp"]), str(e["origin"]), int(e["sequence"])) for e in events]
        self.assertEqual(keys, sorted(keys))

    def test_timeline_records_worker_transition(self):
        result = self.imported("timeline-worker")
        run_id = result["run"]["run_id"]
        self.run_native_once()
        view = StageTimelineService(self.context).timeline(run_id)
        transitions = [
            e["payload"].get("to_state")
            for e in view["events"]
            if e["origin"] == "canonical_persistence"
        ]
        self.assertIn("RUNNING", transitions)
        self.assertIn("SUCCEEDED", transitions)

    def test_timeline_records_queue_ack(self):
        result = self.imported("timeline-ack")
        run_id = result["run"]["run_id"]
        self.run_native_once()
        view = StageTimelineService(self.context).timeline(run_id)
        qtypes = [e["event_type"] for e in view["events"] if e["origin"] == "canonical_queue"]
        self.assertIn("ACKED", qtypes)

    def test_draft_timeline_has_only_operator_events(self):
        run = self.create("timeline-draft")
        view = StageTimelineService(self.context).timeline(run["run_id"])
        self.assertEqual({e["origin"] for e in view["events"]}, {"operator"})

    def test_event_count_matches_events(self):
        result = self.imported("timeline-count")
        view = StageTimelineService(self.context).timeline(result["run"]["run_id"])
        self.assertEqual(view["event_count"], len(view["events"]))


if __name__ == "__main__":
    import unittest
    unittest.main()
