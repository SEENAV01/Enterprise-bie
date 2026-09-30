from __future__ import annotations

from .support import AppProductCase


class StageTimelineTests(AppProductCase):
    def test_created_run_has_source_stored_transition(self):
        job_id = self.create().job_id
        timeline = self.service.timeline(job_id)
        self.assertEqual(timeline.stage_events[0]["reason"], "source_stored")
        self.assertEqual(timeline.stage_events[0]["to_state"], "READY")

    def test_created_run_has_enqueue_event(self):
        job_id = self.create().job_id
        events = self.service.timeline(job_id).queue_events
        self.assertEqual(events[0]["event_type"], "ENQUEUED")

    def test_success_timeline_contains_running_and_success(self):
        job_id = self.create().job_id
        self.service.run_once()
        states = [x["to_state"] for x in self.service.timeline(job_id).stage_events]
        self.assertIn("RUNNING", states)
        self.assertIn("SUCCEEDED", states)

    def test_success_queue_timeline_contains_delivery_and_ack(self):
        job_id = self.create().job_id
        self.service.run_once()
        kinds = [x["event_type"] for x in self.service.timeline(job_id).queue_events]
        self.assertEqual(kinds, ["ENQUEUED", "DELIVERED", "ACKED"])

    def test_stage_sequence_is_persisted_order(self):
        job_id = self.create().job_id
        self.service.run_once()
        seq = [x["sequence"] for x in self.service.timeline(job_id).stage_events]
        self.assertEqual(seq, sorted(seq))
        self.assertEqual(len(seq), len(set(seq)))

    def test_queue_sequence_is_persisted_order(self):
        job_id = self.create().job_id
        self.service.run_once()
        seq = [x["sequence"] for x in self.service.timeline(job_id).queue_events]
        self.assertEqual(seq, sorted(seq))
        self.assertEqual(len(seq), len(set(seq)))

    def test_control_events_are_separate_not_fake_merged(self):
        job_id = self.create().job_id
        self.service.pause(job_id)
        timeline = self.service.timeline(job_id)
        self.assertEqual(timeline.control_events[-1]["action"], "PAUSE")
        self.assertTrue(timeline.stage_events)
        self.assertTrue(timeline.queue_events)

    def test_timeline_survives_restart(self):
        job_id = self.create().job_id
        before = self.service.timeline(job_id).to_safe_dict()
        self.service.close()
        from bie.app_product.service import OperatorService
        self.service = OperatorService(self.root)
        self.assertEqual(self.service.timeline(job_id).to_safe_dict(), before)


if __name__ == "__main__":
    import unittest
    unittest.main()
