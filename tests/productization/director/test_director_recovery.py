"""Real native Director interruption/recovery; technical evidence only.

Lease expiry is seeded exclusively in tests. No production timeout, provider
retry or resource budget is widened. Committed native results replay under the
same native intent while outer attempts retain their separate recovery history.
"""
from dataclasses import replace
from copy import deepcopy
from contextlib import closing
import json
from pathlib import Path
import secrets
import shutil
import sqlite3
import stat
import sys
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_director_producer import (
    ProducerFixture, Credentials, Principal, Service,
    DirectorProducerControlPlane, PROFILE,
)
from protocol_support import make_stack
from bie.productization.director_storage import native_runtime, DirectorReadPersistence
from bie.infrastructure.persistence import PersistedArtifactRecord, PersistenceError


class WorkerInterrupted(BaseException):
    """Process-loss stand-in deliberately outside ordinary error handling."""


class DirectorReadPersistenceTests(unittest.TestCase):
    """Connection ownership only; genuine SQLite rows, no producer mocks."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "runs.sqlite3"
        self.store = DirectorReadPersistence(self.path)
        self.store.create_run("run", {"STAGE": []})
        self.store.register_artifact(PersistedArtifactRecord(
            "artifact", "test.identity", "sha256", "a" * 64, 1,
            "run", "STAGE", False, {"value": 1}, []))

    def tearDown(self):
        self.store.close()
        self.tmp.cleanup()

    def test_artifact_reads_reuse_handle_but_external_sql_tamper_is_visible(self):
        self.assertEqual(self.store.load_artifact("artifact").metadata, {"value": 1})
        connection = self.store._read_connection
        self.assertIsNotNone(connection)
        self.assertFalse(connection.in_transaction)
        with closing(sqlite3.connect(self.path)) as external:
            with external:
                external.execute("UPDATE artifact_records SET metadata_json=? WHERE artifact_id=?",
                                 ('{"value":2}', "artifact"))
        self.assertEqual(self.store.load_artifact("artifact").metadata, {"value": 2})
        self.assertIs(self.store._read_connection, connection)
        self.assertFalse(connection.in_transaction)

    def test_writers_remain_fresh_and_unknown_run_is_still_rejected(self):
        self.store.load_artifact("artifact")
        connection = self.store._read_connection
        self.store.set_run_state("run", "ACTIVE")
        with self.store._conn() as fresh:
            self.assertIsNot(fresh, connection)
            self.assertEqual(fresh.total_changes, 0)
        with self.assertRaisesRegex(PersistenceError, "run not found"):
            self.store.set_run_state("nonexistent", "ACTIVE")
        self.assertEqual(self.store.load_run_state("run")["run_state"], "ACTIVE")
        self.assertEqual(self.store.load_artifact("artifact").metadata, {"value": 1})

    def test_reader_lifecycle_rejects_active_transaction_and_closed_handle(self):
        self.store.load_artifact("artifact")
        connection = self.store._read_connection
        connection.execute("BEGIN")
        try:
            with self.assertRaisesRegex(Exception, "producer_persistence_transaction_active"):
                self.store.load_artifact("artifact")
        finally:
            connection.rollback()
        self.store.close()
        self.assertIsNone(self.store._read_connection)
        with self.assertRaisesRegex(Exception, "producer_persistence_closed"):
            self.store.load_artifact("artifact")

    def test_nested_artifact_read_is_rejected_without_poisoning_outer_read(self):
        self.store.load_artifact("artifact")
        connection = self.store._read_connection
        rejected = []
        fired = False

        def trace(statement):
            nonlocal fired
            if not fired and statement.startswith("SELECT"):
                fired = True
                try:
                    self.store.load_artifact("artifact")
                except Exception as exc:
                    rejected.append(str(exc))

        connection.set_trace_callback(trace)
        try:
            self.assertEqual(self.store.load_artifact("artifact").metadata, {"value": 1})
        finally:
            connection.set_trace_callback(None)
        self.assertEqual(rejected, ["producer_persistence_reentrant_read"])
        self.assertFalse(connection.in_transaction)
        self.assertFalse(self.store._read_context_active)

    def test_database_path_identity_and_file_kind_are_guarded(self):
        self.store.load_artifact("artifact")
        identity = self.store._read_identity
        for mode in (stat.S_IFLNK, stat.S_IFDIR):
            with self.subTest(file_kind=mode), patch.object(type(self.path), "lstat",
                    return_value=SimpleNamespace(st_dev=identity[0], st_ino=identity[1], st_mode=mode)):
                with self.assertRaisesRegex(Exception, "producer_persistence_path_invalid"):
                    self.store.load_artifact("artifact")
        with patch.object(type(self.path), "lstat", side_effect=FileNotFoundError):
            with self.assertRaisesRegex(Exception, "producer_persistence_path_invalid"):
                self.store.load_artifact("artifact")
        displaced = self.path.with_name("original.sqlite3")
        try:
            self.path.replace(displaced)
        except OSError:
            # Windows may forbid replacing an open SQLite file. Exercise the
            # same lstat identity guard without skipping this required control.
            with patch.object(type(self.path), "lstat", return_value=SimpleNamespace(
                    st_dev=identity[0], st_ino=identity[1] + 1, st_mode=stat.S_IFREG)):
                with self.assertRaisesRegex(Exception, "producer_persistence_path_changed"):
                    self.store.load_artifact("artifact")
        else:
            shutil.copyfile(displaced, self.path)
            with self.assertRaisesRegex(Exception, "producer_persistence_path_changed"):
                self.store.load_artifact("artifact")


class DirectorRecoveryTests(ProducerFixture):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Prepare once through the actual native PDF→PEDAGOGY runtime. Each
        # control gets a closed, isolated on-disk copy; DIRECTOR execution,
        # interruption, lease fencing and recovery still occur afresh in it.
        # This avoids repeated expensive upstream fixture preparation, not any
        # Director or recovery execution, and never checks in runtime content.
        fixture = ProducerFixture()
        try:
            fixture.setUp()
        except BaseException:
            if hasattr(fixture, "tmp"):
                fixture.tearDown()
            raise
        cls.prepared = fixture
        cls.addClassCleanup(fixture.tearDown)
        # Every native context in until_director() closes before returning.
        # unittest also runs the registered cleanup if preparation fails.
        fixture.until_director()

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        shutil.copytree(self.prepared.root, self.root, dirs_exist_ok=True)
        self.credentials = Credentials()
        self.token = secrets.token_urlsafe(40)
        self.p = Principal("task033-recovery", "local", frozenset({
            "read", "source", "create", "worker", "control", "admin_recover"}), time.time() + 900)
        self.credentials.grant(self.token, self.p)
        self.operator = Service(self.root, self.credentials)
        self.stack = make_stack()
        self.config = deepcopy(self.prepared.config)
        self.port = DirectorProducerControlPlane(self.operator, enabled_profiles={PROFILE})
        self.source = self.operator.source(self.p, self.prepared.source["source_id"])
        self.run = self.prepared.run

    def until_director(self, run=None):
        result = self.port.status(self.p, run or self.run)
        self.assertEqual(result["stages"]["PEDAGOGY"], "SUCCEEDED")
        self.assertEqual(result["stages"]["DIRECTOR"], "READY")
        return result

    def complete(self, run=None):
        return self.step(run)

    def crash(self, phase):
        self.until_director()

        def fault(current):
            if current == phase:
                raise WorkerInterrupted()

        with self.assertRaises(WorkerInterrupted):
            self.step(fault=fault)

    def expire_test_leases(self, *, native=True, outer=True):
        # Explicit test-only clock seeding; no sleep/polling or production hook.
        with self.port.native(self.p, self.run, "read") as service:
            if outer:
                with service.leases.db:
                    service.leases.db.execute(
                        "UPDATE director_leases SET expires_at=0 WHERE state='ACTIVE'")
            path = service.root / "director-state.sqlite3"
            if native and path.exists():
                with closing(sqlite3.connect(path)) as db:
                    with db:
                        db.execute("UPDATE director_leases SET expires_at=0 WHERE state='ACTIVE'")

    def recover_and_finish(self):
        self.expire_test_leases()
        self.port.recover(self.p, self.run)
        result = self.step()
        self.assertEqual(result["stages"]["DIRECTOR"], "SUCCEEDED")
        self.assertTrue(result["slice_complete"])
        self.assertTrue(all(state == "NOT_RUN" for state in result["downstream"].values()))
        return result

    def native_checkpoint(self):
        with self.port.native(self.p, self.run, "read") as service:
            with native_runtime(service, self.run, None) as runtime:
                rows = [r for r in runtime.io.catalog.records.values()
                        if r.artifact_type == "director.plan"]
                self.assertEqual(len(rows), 1)
                envelope = runtime.io.load(rows[0].artifact_id)
                return envelope.to_ref()

    def committed_replay(self, phase):
        self.crash(phase)
        expected = self.native_checkpoint()
        calls = dict(self.stack.calls)
        self.recover_and_finish()
        output, receipt = self.native_result()
        self.assertEqual(output.to_ref(), expected)
        self.assertEqual(self.stack.calls, calls)
        self.assertEqual(receipt["native_attempt"], 1)

    def crash_provider(self, role, operation=None):
        self.until_director()
        provider = getattr(self.stack, role)
        invoke = provider.invoke
        fired = False

        def interrupted(request):
            nonlocal fired
            payload = json.loads(request.messages[1]["content"])
            if not fired and (operation is None or payload.get("operation") == operation):
                fired = True
                raise WorkerInterrupted()
            return invoke(request)

        provider.invoke = interrupted
        try:
            with self.assertRaises(WorkerInterrupted):
                self.step()
        finally:
            provider.invoke = invoke
        self.assertTrue(fired)
        self.recover_and_finish()

    def test_native_input_validation_interruption(self):
        self.crash("after_DIRECTOR_input_validation")
        self.assertEqual(self.stack.calls, dict(generator=0, critic=0, annotator=0, reviewer=0))
        self.recover_and_finish()

    def test_generator_plan_interruption(self):
        self.crash_provider("generator", "PLAN")

    def test_generator_narration_interruption(self):
        self.crash_provider("generator", "NARRATE")

    def test_factual_critic_interruption(self):
        self.crash_provider("critic")

    def test_annotation_generation_interruption(self):
        self.crash_provider("annotator")

    def test_annotation_review_interruption(self):
        self.crash_provider("reviewer")

    def test_native_base_evidence_cas_interruption(self):
        self.crash("after_DIRECTOR_native_evidence.director_base_execution_cas")
        self.recover_and_finish()

    def test_native_base_evidence_index_interruption(self):
        self.crash("after_DIRECTOR_native_evidence.director_base_execution_index")
        with self.port.native(self.p, self.run, "read") as service:
            with native_runtime(service, self.run, None) as runtime:
                self.assertTrue(any(r.artifact_type == "evidence.director_base_execution"
                                    for r in runtime.io.catalog.records.values()))
        self.recover_and_finish()

    def test_native_annotation_evidence_cas_interruption(self):
        self.crash("after_DIRECTOR_native_evidence.director_execution_cas")
        self.recover_and_finish()

    def test_native_annotation_evidence_index_interruption(self):
        self.crash("after_DIRECTOR_native_evidence.director_execution_index")
        self.recover_and_finish()

    def test_native_plan_cas_interruption(self):
        self.crash("after_DIRECTOR_native_director.plan_cas")
        self.recover_and_finish()

    def test_native_plan_index_interruption(self):
        self.crash("after_DIRECTOR_native_director.plan_index")
        expected = self.native_checkpoint()
        self.recover_and_finish()
        self.assertEqual(self.native_result()[0].to_ref(), expected)

    def test_native_commit_before_outer_execution_return_replays_without_calls(self):
        self.committed_replay("after_DIRECTOR_native_execution")

    def test_native_commit_before_outer_index_bridge_replays_without_calls(self):
        self.committed_replay("after_DIRECTOR_native_bridge")

    def test_safe_receipt_cas_before_outer_commit_replays_without_calls(self):
        self.committed_replay("after_DIRECTOR_producer.evidence_cas")

    def test_terminal_before_queue_ack_keeps_exact_identity(self):
        self.crash("after_DIRECTOR_terminal")
        expected = self.native_checkpoint()
        calls = dict(self.stack.calls)
        with self.port.native(self.p, self.run, "read") as service:
            before = service.persistence.load_run_state(self.run)["stages"]["DIRECTOR"]["attempts"][-1]
            self.assertEqual(before["state"], "SUCCEEDED")
            task = service.task_id(self.run, "DIRECTOR", before["attempt"])
            self.assertEqual(service.queue.get(task).state, "DELIVERED")
        self.recover_and_finish()
        output, receipt = self.native_result()
        self.assertEqual(output.to_ref(), expected)
        self.assertEqual(self.stack.calls, calls)
        with self.port.native(self.p, self.run, "read") as service:
            after = service.persistence.load_run_state(self.run)["stages"]["DIRECTOR"]["attempts"][-1]
            self.assertEqual(after["attempt"], before["attempt"])
            self.assertEqual(service.queue.get(task).state, "ACKED")

    def test_ack_before_downstream_boundary_does_not_execute_visual(self):
        self.crash("before_next_admission")
        expected = self.native_checkpoint()
        calls = dict(self.stack.calls)
        result = self.step()
        self.assertTrue(result["slice_complete"])
        self.assertEqual(self.native_result()[0].to_ref(), expected)
        self.assertEqual(self.stack.calls, calls)
        self.assertTrue(all(v == "NOT_RUN" for v in result["downstream"].values()))

    def test_live_outer_lease_cannot_be_reclaimed(self):
        self.crash("after_DIRECTOR_input_validation")
        with self.assertRaises(Exception):
            self.port.recover(self.p, self.run)

    def test_live_native_lease_cannot_be_reclaimed(self):
        self.until_director()
        invoke = self.stack.generator.invoke
        self.stack.generator.invoke = lambda _: (_ for _ in ()).throw(WorkerInterrupted())
        try:
            with self.assertRaises(WorkerInterrupted):
                self.step()
        finally:
            self.stack.generator.invoke = invoke
        self.expire_test_leases(native=False)
        self.port.recover(self.p, self.run)
        result = self.step()
        self.failed(result)
        with self.port.native(self.p, self.run, "read") as service:
            with native_runtime(service, self.run, None) as runtime:
                active = runtime.recovery.leases.db.execute(
                    "SELECT state,epoch FROM director_leases").fetchall()
                self.assertEqual(active, [("ACTIVE", 1)])

    def test_stale_native_catalog_writer_is_rejected(self):
        self.until_director()
        with self.port.native(self.p, self.run, "worker") as service:
            with native_runtime(service, self.run, None) as runtime:
                request, _, _ = service.request(self.run, self.p.tenant)
                service.active_lease = service.leases.acquire(
                    "test-stale-director", "intent", service.owner, now=0, ttl_seconds=1)
                with self.assertRaises(Exception):
                    runtime.io.derive("evidence.test_stale", self.run,
                        (request.pedagogy_ref,), dict(technical=True), stage_id="DIRECTOR",
                        metadata=dict(requires_review=True, accepted=False), evidence=True)

    def test_competing_outer_worker_cannot_complete(self):
        self.until_director()
        with self.port.native(self.p, self.run, "read") as service:
            config = service.configuration(self.run, self.p.tenant)
            task = service.task_id(self.run, "DIRECTOR", 1)
            service.leases.acquire(task, config["fingerprint"], "competing-live-worker", ttl_seconds=120)
        with self.assertRaises(Exception):
            self.step()
        self.assertEqual(self.stack.calls, dict(generator=0, critic=0, annotator=0, reviewer=0))
        with self.port.native(self.p, self.run, "read") as service:
            self.assertNotEqual(service.queue.get(task).state, "ACKED")

    def test_interrupted_outer_attempt_is_retained_without_native_revision_bump(self):
        self.crash("after_DIRECTOR_native_execution")
        self.recover_and_finish()
        with self.port.native(self.p, self.run, "read") as service:
            attempts = service.persistence.load_run_state(self.run)["stages"]["DIRECTOR"]["attempts"]
            self.assertEqual([row["state"] for row in attempts], ["FAILED", "SUCCEEDED"])
            self.assertTrue(attempts[0]["evidence_refs"])
            self.assertEqual(service.queue.get(service.task_id(self.run, "DIRECTOR", 1)).state,
                             "DEAD_LETTER")
            self.assertEqual(service.queue.get(service.task_id(self.run, "DIRECTOR", 2)).state,
                             "ACKED")
        self.assertEqual(self.native_result()[1]["native_attempt"], 1)

    def test_committed_tamper_cannot_be_recovery_acked(self):
        self.crash("after_DIRECTOR_terminal")
        self.tamper_stage("DIRECTOR")
        self.expire_test_leases()
        with self.assertRaises(Exception):
            self.port.recover(self.p, self.run)
        with self.port.native(self.p, self.run, "read") as service:
            self.assertEqual(service.queue.get(service.task_id(self.run, "DIRECTOR", 1)).state,
                             "DELIVERED")

    def test_native_index_tamper_blocks_restart(self):
        self.assertTrue(self.complete()["slice_complete"])
        with self.port.native(self.p, self.run, "read") as service:
            with closing(sqlite3.connect(service.root / "director-catalog.sqlite3")) as db:
                with db:
                    db.execute("UPDATE artifact_records SET record_json='{}' WHERE artifact_id=?",
                               (self.native_result()[0].artifact_id,))
        with self.assertRaises(Exception):
            self.port.status(self.p, self.run)

    def test_deliberate_native_revision_has_new_identity_not_old_replay(self):
        self.assertTrue(self.complete()["slice_complete"])
        with self.port.native(self.p, self.run, "worker") as service:
            request, _, _ = service.request(self.run, self.p.tenant)
            with native_runtime(service, self.run, self.stack) as assembly:
                first = assembly.execute(request)
                calls = dict(self.stack.calls)
                revised = replace(request, idempotency_key=request.idempotency_key + ":revision-2",
                                  attempt=2, previous_idempotency_key=request.idempotency_key)
                second = assembly.execute(revised)
                self.assertNotEqual(first.output_artifact_refs, second.output_artifact_refs)
                self.assertGreater(self.stack.calls["critic"], calls["critic"])
                current = assembly.executor.revisions.get(self.run, request.lesson_id)
                self.assertEqual(current.attempt, 2)
                with self.assertRaises(Exception):
                    assembly.consumers()._director(first.output_artifact_refs[0])

    def test_invalid_native_revision_cannot_replay_committed_result(self):
        self.assertTrue(self.complete()["slice_complete"])
        with self.port.native(self.p, self.run, "worker") as service:
            request, _, _ = service.request(self.run, self.p.tenant)
            with native_runtime(service, self.run, self.stack) as assembly:
                invalid = replace(request, attempt=2)
                calls = dict(self.stack.calls)
                with self.assertRaises(Exception):
                    assembly.execute(invalid)
                self.assertEqual(self.stack.calls, calls)

    def test_completed_recovery_is_identity_bound_without_provider_calls(self):
        expected = self.complete()
        self.assertTrue(expected["slice_complete"])
        calls = dict(self.stack.calls)
        self.assertEqual(self.port.recover(self.p, self.run), expected)
        self.assertEqual(self.stack.calls, calls)
        with self.port.native(self.p, self.run, "read") as service:
            self.assertEqual(len(service.persistence.load_run_state(self.run)
                ["stages"]["DIRECTOR"]["attempts"]), 1)


if __name__ == "__main__":
    unittest.main()
