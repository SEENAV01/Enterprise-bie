"""Task028A deterministic restart fixture and safe diagnostic regressions."""
from contextlib import redirect_stdout
import gc
import hashlib
import io
import json
from pathlib import Path
import queue
import sys
import tempfile
import threading
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from scripts import smoke_bie_local_stack as smoke


class SmokeRegressionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="bie-task028a-")
        self.root = Path(self.temp.name)
    def tearDown(self):
        gc.collect()
        self.temp.cleanup()
    def status(self, job):
        service = smoke.PdfInspectionJobService(self.root)
        try:
            return service.status(job['job_id'])
        finally:
            service.close()
    def gated_worker(self):
        release, waiting = threading.Event(), threading.Event()
        outcomes = queue.Queue()
        def work():
            waiting.set()
            if not release.wait(10):
                outcomes.put('START_GATE_TIMEOUT')
                return
            service = smoke.PdfInspectionJobService(self.root)
            try:
                outcomes.put(service.run_once('seeded-startup-gate').outcome)
            except Exception:
                outcomes.put('WORKER_ERROR')
            finally:
                service.close()
        thread = threading.Thread(target=work)
        thread.start()
        self.assertTrue(waiting.wait(5))
        return release, outcomes, thread

    def test_ready_setup_uses_no_sleep_or_subprocess(self):
        with (patch.object(smoke.time, 'sleep', side_effect=AssertionError('no timing fixture')),
              patch.object(smoke.subprocess, 'Popen', side_effect=AssertionError('no worker during fixture'))):
            job = smoke.prepare_restart_job(self.root)
        self.assertEqual(self.status(job)['status'], 'READY')
        self.assertEqual(self.status(job)['queue_state'], 'READY')

    def test_setup_reopens_real_sqlite_and_verifies_cas_identity(self):
        job = smoke.prepare_restart_job(self.root)
        service = smoke.PdfInspectionJobService(self.root)
        try:
            state = service.persistence.load_run_state(job['job_id'])
            source_id = state['stages']['PDF_INSPECTION']['attempts'][0]['input_artifact_refs'][0]
            data = service._source_bytes(source_id)
            self.assertEqual(hashlib.sha256(data).hexdigest(), job['source_hash'])
            self.assertTrue(data.startswith(b'%PDF'))
            self.assertEqual(smoke.persisted_states(self.root, job['job_id']), ['READY'])
        finally:
            service.close()

    def test_restart_fixture_independent_of_delayed_worker_startup(self):
        release, outcomes, thread = self.gated_worker()
        try:
            # Worker cannot execute a first poll until the explicit gate opens.
            # No chosen number of seconds establishes the READY proof.
            with patch.object(smoke.time, 'sleep', side_effect=AssertionError('fixed sleep forbidden')):
                job = smoke.prepare_restart_job(self.root)
                self.assertEqual(self.status(job)['queue_state'], 'READY')
                self.assertFalse(release.is_set())
            release.set()
            self.assertEqual(outcomes.get(timeout=10), 'ACKED')
            self.assertEqual(self.status(job)['status'], 'SUCCEEDED')
        finally:
            release.set()
            thread.join(10)
        self.assertFalse(thread.is_alive())

    def test_late_first_poll_consumes_old_pending_window_negative_control(self):
        release, outcomes, thread = self.gated_worker()
        service = smoke.PdfInspectionJobService(self.root)
        try:
            # Reproduce the old assumption's counterexample: first poll occurs
            # AFTER submission, regardless of an earlier elapsed startup delay.
            job = service.submit(smoke.structural_pdf(text_pages={0}), 'late-first-poll')
            self.assertEqual(service.status(job['job_id'])['queue_state'], 'READY')
            release.set()
            self.assertEqual(outcomes.get(timeout=10), 'ACKED')
            self.assertNotEqual(service.status(job['job_id'])['queue_state'], 'READY')
        finally:
            release.set()
            thread.join(10)
            service.close()
        self.assertFalse(thread.is_alive())

    def test_ready_gate_rejects_already_consumed_fixture(self):
        smoke.prepare_restart_job(self.root)
        service = smoke.PdfInspectionJobService(self.root)
        try:
            self.assertEqual(service.run_once('negative-control').outcome, 'ACKED')
        finally:
            service.close()
        with self.assertRaisesRegex(smoke.SmokeCheck, '^restart_ready_state_failed$'):
            smoke.prepare_restart_job(self.root)

    def test_each_phase_redacts_unexpected_exception(self):
        for name in smoke.PHASES:
            with self.subTest(phase=name), redirect_stdout(io.StringIO()):
                with self.assertRaises(smoke.SmokeFailure) as raised:
                    with smoke.phase(name):
                        raise ValueError('PRIVATE-PATH SECRET PDF CONTENT')
                report = raised.exception.safe_report()
                self.assertEqual(report['phase'], name)
                self.assertEqual(report['code'], name + '_failed')
                self.assertNotIn('PRIVATE', json.dumps(report))

    def test_known_assertion_code_survives_without_traceback(self):
        output = io.StringIO()
        with redirect_stdout(output), self.assertRaises(smoke.SmokeFailure) as raised:
            with smoke.phase('pre_restart_ready_state'):
                smoke.require(False, 'restart_ready_state_failed')
        self.assertEqual(raised.exception.safe_report()['code'], 'restart_ready_state_failed')
        self.assertNotIn('Traceback', output.getvalue())

    def test_untrusted_phase_and_code_are_not_echoed(self):
        report = smoke.SmokeFailure('PRIVATE-PATH', 'SECRET').safe_report()
        self.assertEqual((report['phase'], report['code']), ('smoke', 'smoke_failed'))

    def test_cleanup_retains_primary_failure_and_records_secondary(self):
        process = Mock()
        process.stop.side_effect = RuntimeError('PRIVATE-PATH')
        with redirect_stdout(io.StringIO()), self.assertRaises(smoke.SmokeFailure) as raised:
            try:
                raise smoke.SmokeFailure('success_lifecycle', 'result_identity_failed')
            finally:
                smoke.finish_process(process, {}, 'shutdown')
        report = raised.exception.safe_report()
        self.assertEqual(report['code'], 'result_identity_failed')
        self.assertEqual(report['cleanup_failures'], [{'phase': 'shutdown', 'code': 'shutdown_failed'}])

    def test_shutdown_failure_cannot_be_marked_pass(self):
        process = Mock()
        process.stop.side_effect = RuntimeError('PRIVATE-PATH')
        with redirect_stdout(io.StringIO()), self.assertRaises(smoke.SmokeFailure) as raised:
            smoke.finish_process(process, {}, 'shutdown')
        self.assertEqual(raised.exception.phase, 'shutdown')

    def test_cli_writes_safe_failure_evidence_and_nonzero_exit(self):
        failure = smoke.SmokeFailure('restart_lifecycle', 'restart_result_failed')
        with patch.object(smoke, 'smoke', side_effect=failure), redirect_stdout(io.StringIO()) as output:
            code = smoke.main(['--evidence-dir', str(self.root)])
        self.assertEqual(code, 1)
        saved = json.loads((self.root / 'safe-stack-lifecycle.json').read_text())
        self.assertEqual(saved, json.loads(output.getvalue()))
        self.assertEqual(saved['phase'], 'restart_lifecycle')
        self.assertNotIn(str(self.root), json.dumps(saved))

    def test_cli_redacts_unknown_exception(self):
        with (patch.object(smoke, 'smoke', side_effect=RuntimeError('SECRET PATH')),
              redirect_stdout(io.StringIO()) as output):
            self.assertEqual(smoke.main([]), 1)
        self.assertNotIn('SECRET', output.getvalue())
        self.assertEqual(json.loads(output.getvalue())['code'], 'smoke_failed')


if __name__ == '__main__':
    unittest.main()
