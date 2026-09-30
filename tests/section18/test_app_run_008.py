from __future__ import annotations

from batch001_support import OperatorCase

from bie.product_app_v1.models import OperatorConflict
from bie.product_app_v1.run_control import RunControlService


class AppRun008Tests(OperatorCase):
    def test_pause_moves_ready_task_out_of_queue(self):
        result = self.imported("pause")
        run_id = result["run"]["run_id"]
        value = RunControlService(self.context).pause(run_id)
        self.assertEqual(value["state"], "PAUSED")
        service = self.context.job_service()
        try:
            delivery = service.queue.get("inspect-" + result["canonical_job"]["job_id"][4:])
        finally:
            service.close()
        self.assertEqual(delivery.state, "DEAD_LETTER")
        self.assertEqual(delivery.last_reason, "operator_pause")

    def test_resume_redrives_paused_task(self):
        result = self.imported("resume")
        run_id = result["run"]["run_id"]
        controls = RunControlService(self.context)
        controls.pause(run_id)
        value = controls.resume(run_id)
        self.assertEqual(value["state"], "READY")
        service = self.context.job_service()
        try:
            delivery = service.queue.get("inspect-" + result["canonical_job"]["job_id"][4:])
        finally:
            service.close()
        self.assertEqual(delivery.state, "READY")

    def test_cancel_ready_dead_letters_task(self):
        result = self.imported("cancel-ready")
        run_id = result["run"]["run_id"]
        value = RunControlService(self.context).cancel(run_id)
        self.assertEqual(value["state"], "CANCELLED")
        service = self.context.job_service()
        try:
            delivery = service.queue.get("inspect-" + result["canonical_job"]["job_id"][4:])
        finally:
            service.close()
        self.assertEqual(delivery.state, "DEAD_LETTER")
        self.assertEqual(delivery.last_reason, "operator_cancel")

    def test_cancel_draft_has_no_fake_queue_action(self):
        run = self.create("cancel-draft")
        value = RunControlService(self.context).cancel(run["run_id"])
        self.assertEqual(value["state"], "CANCELLED")
        self.assertEqual(self.context.operator.get_run(run["run_id"]).attempt, 0)

    def test_cancel_paused_is_terminal(self):
        result = self.imported("cancel-paused")
        run_id = result["run"]["run_id"]
        controls = RunControlService(self.context)
        controls.pause(run_id)
        self.assertEqual(controls.cancel(run_id)["state"], "CANCELLED")
        with self.assertRaises(OperatorConflict):
            controls.resume(run_id)

    def test_pause_rejects_in_flight_delivery(self):
        result = self.imported("pause-inflight")
        run_id = result["run"]["run_id"]
        service = self.context.job_service()
        try:
            task = service.queue.poll("other-worker", capability_tags=["pdf_inspection"])
            self.assertIsNotNone(task)
        finally:
            service.close()
        with self.assertRaises(OperatorConflict):
            RunControlService(self.context).pause(run_id)

    def test_cancel_rejects_in_flight_delivery(self):
        result = self.imported("cancel-inflight")
        run_id = result["run"]["run_id"]
        service = self.context.job_service()
        try:
            task = service.queue.poll("other-worker", capability_tags=["pdf_inspection"])
            self.assertIsNotNone(task)
        finally:
            service.close()
        with self.assertRaises(OperatorConflict):
            RunControlService(self.context).cancel(run_id)

    def test_pause_resume_events_are_persisted(self):
        result = self.imported("control-events")
        run_id = result["run"]["run_id"]
        controls = RunControlService(self.context)
        controls.pause(run_id)
        controls.resume(run_id)
        names = [e.event_type for e in self.context.operator.events(run_id)]
        self.assertIn("RUN_PAUSED", names)
        self.assertIn("RUN_RESUMED", names)

    def test_paused_state_survives_restart(self):
        result = self.imported("pause-restart")
        run_id = result["run"]["run_id"]
        RunControlService(self.context).pause(run_id)
        from bie.product_app_v1.context import OperatorContext
        reopened = OperatorContext(self.root)
        self.assertEqual(reopened.operator.get_run(run_id).state, "PAUSED")

    def test_worker_does_not_consume_paused_task(self):
        result = self.imported("pause-worker")
        run_id = result["run"]["run_id"]
        RunControlService(self.context).pause(run_id)
        self.assertEqual(self.run_native_once().outcome, "IDLE")
        self.assertEqual(self.context.operator.get_run(run_id).state, "PAUSED")

    def test_worker_can_consume_after_resume(self):
        result = self.imported("resume-worker")
        run_id = result["run"]["run_id"]
        controls = RunControlService(self.context)
        controls.pause(run_id)
        controls.resume(run_id)
        self.assertEqual(self.run_native_once().outcome, "ACKED")


if __name__ == "__main__":
    import unittest
    unittest.main()
