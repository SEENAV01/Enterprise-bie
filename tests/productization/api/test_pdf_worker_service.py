"""Task028 worker behavior and legacy CLI compatibility; no operator dispatch."""
from __future__ import annotations
import gc
import json
import os
import signal
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests/productization/document_intelligence"))
from apps.api.job_service import PdfInspectionJobService, WorkerOutcome
from apps.api.pdf_worker_service import PdfInspectionWorkerService, WorkerServiceError, api_worker_root, stop_signals
from structural_pdf_fixtures import structural_pdf


class Stop:
    def __init__(self):
        self.stopped = False
        self.waits = []
    def is_set(self):
        return self.stopped
    def set(self):
        self.stopped = True
    def wait(self, seconds):
        self.waits.append(seconds)
        self.set()
        return True


class WorkerServiceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="bie-task028-unit-")
        self.root = Path(self.temp.name)
        self.jobs = Mock(data_root=self.root)
        self.stop = Stop()
    def tearDown(self):
        gc.collect()
        self.temp.cleanup()
    def worker(self, **kwargs):
        return PdfInspectionWorkerService(self.jobs, **kwargs)
    def cli(self, *args):
        return subprocess.run([sys.executable, "-B", str(ROOT / "scripts/run_bie_pdf_worker.py"), *args],
                              env={**os.environ, "BIE_DATA_ROOT": str(self.root)},
                              capture_output=True, text=True, timeout=30, cwd=ROOT)

    def test_default_interval_one_second(self):
        self.assertEqual(self.worker().poll_interval, 1.0)
    def test_idle_wait_is_bounded_and_counted(self):
        self.jobs.run_once.return_value = WorkerOutcome("IDLE")
        summary = self.worker(poll_interval=0.25).run(self.stop)
        self.assertEqual(self.stop.waits, [0.25])
        self.assertEqual(summary.idle_polls, 1)
        self.jobs.run_once.assert_called_once_with("bie-pdf-worker-local")
    def test_invalid_intervals_fail_closed(self):
        for interval in (0, -1, .099, 60.001, float("inf"), float("nan"), True, "1", None):
            with self.subTest(interval=repr(interval)), self.assertRaises(ValueError):
                self.worker(poll_interval=interval)
    def test_exact_interval_boundaries_accepted(self):
        for interval in (.1, 60):
            self.assertEqual(self.worker(poll_interval=interval).poll_interval, interval)
    def test_acked_and_failed_counted_without_job_identity_leak(self):
        self.jobs.run_once.side_effect = [WorkerOutcome("ACKED", "private-document"), WorkerOutcome("FAILED"), WorkerOutcome("IDLE")]
        self.assertEqual(self.worker().run(self.stop).to_safe_dict(),
                         {"jobs_acked": 1, "jobs_failed": 1, "idle_polls": 1})
    def test_failed_document_does_not_end_service(self):
        self.jobs.run_once.side_effect = [WorkerOutcome("FAILED"), WorkerOutcome("ACKED"), WorkerOutcome("IDLE")]
        summary = self.worker().run(self.stop)
        self.assertEqual((summary.jobs_failed, summary.jobs_acked), (1, 1))
        self.assertEqual(self.jobs.run_once.call_count, 3)
    def test_preexisting_stop_fetches_nothing(self):
        self.stop.set()
        self.worker().run(self.stop)
        self.jobs.run_once.assert_not_called()
    def test_stop_during_job_allows_completion_without_new_fetch(self):
        def finish(worker_id):
            self.stop.set()
            return WorkerOutcome("ACKED")
        self.jobs.run_once.side_effect = finish
        self.assertEqual(self.worker().run(self.stop).jobs_acked, 1)
        self.jobs.run_once.assert_called_once()
    def test_idle_real_event_is_interruptible(self):
        self.jobs.run_once.return_value = WorkerOutcome("IDLE")
        event = threading.Event()
        entered = threading.Event()
        self.jobs.run_once.side_effect = lambda _: (entered.set(), WorkerOutcome("IDLE"))[1]
        worker = self.worker(poll_interval=60)
        thread = threading.Thread(target=worker.run, args=(event,))
        thread.start()
        try:
            self.assertTrue(entered.wait(2))
            event.set()
            thread.join(2)
            self.assertFalse(thread.is_alive())
        finally:
            event.set()
            thread.join(2)
    def test_real_stop_signals_set_event_and_restore_handlers(self):
        for sig in (signal.SIGINT, signal.SIGTERM):
            with self.subTest(signal=sig):
                event = threading.Event()
                before = signal.getsignal(sig)
                with stop_signals(event):
                    signal.raise_signal(sig)
                    self.assertTrue(event.is_set())
                self.assertEqual(signal.getsignal(sig), before)
    def test_fatal_service_exception_is_safe_and_not_retried(self):
        self.jobs.run_once.side_effect = RuntimeError("secret-path-and-text")
        with self.assertRaisesRegex(WorkerServiceError, "^worker_service_failed$"):
            self.worker().run(self.stop)
        self.jobs.run_once.assert_called_once()
    def test_unknown_outcome_fails_closed(self):
        self.jobs.run_once.return_value = WorkerOutcome("SUCCEEDED")
        with self.assertRaises(WorkerServiceError):
            self.worker().run(self.stop)
    def test_summary_contains_only_three_safe_counters(self):
        self.jobs.run_once.return_value = WorkerOutcome("IDLE", str(self.root), "private textbook")
        safe = json.dumps(self.worker().run(self.stop).to_safe_dict())
        self.assertNotIn(str(self.root), safe)
        self.assertNotIn("textbook", safe)
        self.assertEqual(set(json.loads(safe)), {"jobs_acked", "jobs_failed", "idle_polls"})
    def test_worker_id_is_passed_to_canonical_service(self):
        self.jobs.run_once.return_value = WorkerOutcome("IDLE")
        self.worker(worker_id="worker.028-1").run(self.stop)
        self.jobs.run_once.assert_called_once_with("worker.028-1")
    def test_invalid_worker_id_is_rejected(self):
        for value in ("", "a" * 129, "worker\nsecret", "path/name", None):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.worker(worker_id=value)
    def test_operator_root_is_rejected_before_poll(self):
        (self.root / "operator.sqlite3").touch()
        with self.assertRaises(WorkerServiceError):
            self.worker().run(self.stop)
        self.jobs.run_once.assert_not_called()
    def test_operator_per_run_descendant_is_rejected(self):
        (self.root / "operator.sqlite3").touch()
        with self.assertRaisesRegex(WorkerServiceError, "operator_namespace_forbidden"):
            api_worker_root(self.root / "runs" / "run-123")
        self.assertFalse((self.root / "runs").exists())
    def test_namespace_is_rechecked_between_jobs(self):
        def first(worker_id):
            (self.root / "operator.sqlite3").touch()
            return WorkerOutcome("ACKED")
        self.jobs.run_once.side_effect = first
        with self.assertRaises(WorkerServiceError):
            self.worker().run(self.stop)
        self.jobs.run_once.assert_called_once()
    def test_three_real_persisted_jobs_are_sequentially_processed(self):
        jobs = PdfInspectionJobService(self.root)
        try:
            ids = [jobs.submit(structural_pdf(text_pages={0}, text=f"Synthetic source {i}"), f"worker-{i}")["job_id"] for i in range(3)]
            actual = jobs.run_once
            calls = []
            def record(worker_id):
                result = actual(worker_id)
                calls.append(result.outcome)
                return result
            with patch.object(jobs, "run_once", side_effect=record):
                summary = PdfInspectionWorkerService(jobs).run(self.stop)
            self.assertEqual(calls, ["ACKED", "ACKED", "ACKED", "IDLE"])
            self.assertEqual(summary.jobs_acked, 3)
            self.assertTrue(all(jobs.status(i)["status"] == "SUCCEEDED" for i in ids))
        finally:
            jobs.close()
    def test_once_cli_retains_idle_default(self):
        result = self.cli()
        self.assertEqual((result.returncode, json.loads(result.stdout)), (0, {"outcome": "IDLE"}))
    def test_explicit_once_processes_real_job(self):
        jobs = PdfInspectionJobService(self.root)
        try:
            submitted = jobs.submit(structural_pdf(text_pages={0}), "once")
            result = self.cli("--once")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["outcome"], "ACKED")
            self.assertEqual(jobs.status(submitted["job_id"])["queue_state"], "ACKED")
        finally:
            jobs.close()
    def test_once_and_serve_mutually_exclusive(self):
        result = self.cli("--once", "--serve")
        self.assertEqual(result.returncode, 2)
        self.assertNotIn("Traceback", result.stderr)
    def test_serve_cli_clean_private_pipe_shutdown(self):
        result = subprocess.run([sys.executable, "-B", str(ROOT / "scripts/run_bie_pdf_worker.py"), "--serve"],
                                input="", capture_output=True, text=True, timeout=30, cwd=ROOT,
                                env={**os.environ, "BIE_DATA_ROOT": str(self.root), "BIE_PDF_WORKER_CONTROL_STDIN": "1"})
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["outcome"], "STOPPED")
    def test_cli_configuration_and_startup_failures_are_safe(self):
        (self.root / "operator.sqlite3").touch()
        result = self.cli("--serve")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(json.loads(result.stdout), {"outcome": "FAILED"})
        self.assertEqual(result.stderr, "")
    def test_invalid_cli_interval_rejected(self):
        result = self.cli("--serve", "--poll-interval", "nan")
        self.assertEqual(result.returncode, 1)
        self.assertNotIn(str(self.root), result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
