import tempfile
import unittest
from pathlib import Path

from bie.director.director_artifacts import DirectorArtifactIO
from bie.director.director_durable_recovery import (
    DirectorLeaseStore, DirectorRecoveryCoordinator, RecoveryError,
    SQLiteArtifactCatalog,
)
from bie.infrastructure.artifact_store import ArtifactRecord, ArtifactStoreError, FileSystemCAS
from bie.infrastructure.idempotency_store import SQLiteIdempotencyStore


class DurableRecoveryTests(unittest.TestCase):
    def fixture(self):
        temp = tempfile.TemporaryDirectory(); self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        return root, FileSystemCAS(root / 'cas')

    def test_catalog_restarts_with_exact_graph_and_cas_bytes(self):
        root, cas = self.fixture(); path = root / 'catalog.sqlite'
        catalog = SQLiteArtifactCatalog(cas, path)
        first = catalog.put_artifact('source', 'source.document', b'source', 'run', 'INGEST')
        second = catalog.put_artifact('reasoning', 'reasoning.decision_set', b'reasoning', 'run', 'RE', ['source'])
        catalog.close()
        reopened = SQLiteArtifactCatalog(cas, path); self.addCleanup(reopened.close)
        self.assertEqual(reopened.get_record('source'), first)
        self.assertEqual(reopened.get_record('reasoning'), second)
        self.assertEqual(reopened.read_artifact('reasoning'), b'reasoning')
        self.assertEqual(reopened.trace_to_roots('reasoning'), {'source'})
        self.assertEqual(reopened.verify_durable_index(), ())

    def test_catalog_rejects_corrupt_journal_and_missing_cas(self):
        root, cas = self.fixture(); path = root / 'catalog.sqlite'
        catalog = SQLiteArtifactCatalog(cas, path)
        record = catalog.put_artifact('one', 'evidence.test', b'payload', 'run', 'QA')
        blob_path = cas._path(record.blob.digest); catalog.close(); blob_path.write_bytes(b'tampered')
        with self.assertRaises(ArtifactStoreError): SQLiteArtifactCatalog(cas, path)

    def test_catalog_insert_rolls_back_when_parent_is_unknown(self):
        root, cas = self.fixture(); path = root / 'catalog.sqlite'; catalog = SQLiteArtifactCatalog(cas, path)
        self.addCleanup(catalog.close); blob = cas.put_bytes(b'child')
        record = ArtifactRecord('child', 'test.child', blob, 'run', 'DIR', ['missing'])
        with self.assertRaises(ArtifactStoreError): catalog.register(record)
        self.assertIsNone(catalog.db.execute('SELECT artifact_id FROM artifact_records WHERE artifact_id=?', ('child',)).fetchone())

    def test_live_foreign_worker_cannot_be_stolen(self):
        root, _ = self.fixture(); leases = DirectorLeaseStore(root / 'leases.sqlite'); self.addCleanup(leases.close)
        leases.acquire('key', 'sha256:' + '1' * 64, 'worker-a', now=100, ttl_seconds=30)
        with self.assertRaisesRegex(RecoveryError, 'live worker'):
            leases.acquire('key', 'sha256:' + '1' * 64, 'worker-b', now=110, ttl_seconds=30)

    def test_expired_worker_is_reclaimed_with_higher_epoch_and_fence(self):
        root, _ = self.fixture(); leases = DirectorLeaseStore(root / 'leases.sqlite'); self.addCleanup(leases.close)
        old = leases.acquire('key', 'sha256:' + '2' * 64, 'worker-a', now=100, ttl_seconds=10)
        current = leases.acquire('key', old.fingerprint, 'worker-b', now=111, ttl_seconds=30)
        self.assertEqual((old.epoch, current.epoch, current.owner), (1, 2, 'worker-b'))
        with self.assertRaisesRegex(RecoveryError, 'stale'):
            leases.complete(old, 'cas:old', now=112)
        completed = leases.complete(current, 'cas:new', now=112)
        self.assertEqual((completed.state, completed.result_ref), ('COMPLETED', 'cas:new'))

    def test_only_matching_incomplete_idempotency_claim_is_reclaimed(self):
        root, _ = self.fixture(); leases = DirectorLeaseStore(root / 'leases.sqlite'); self.addCleanup(leases.close)
        claims = SQLiteIdempotencyStore(root / 'idempotency.sqlite'); self.addCleanup(claims.close)
        fingerprint = 'sha256:' + '3' * 64
        old = leases.acquire('key', fingerprint, 'worker-a', now=100, ttl_seconds=10)
        claims.claim('key', fingerprint, 'worker-a')
        current = leases.acquire('key', fingerprint, 'worker-b', now=111, ttl_seconds=30)
        reclaimed = leases.reclaim_idempotency(claims, current, 'worker-b', now=112)
        self.assertEqual((reclaimed.state, reclaimed.owner), ('CLAIMED', 'worker-b'))
        with self.assertRaises(RecoveryError): leases.reclaim_idempotency(claims, old, 'worker-a', now=112)

    def test_completed_lease_is_replayable_but_immutable(self):
        root, _ = self.fixture(); leases = DirectorLeaseStore(root / 'leases.sqlite'); self.addCleanup(leases.close)
        lease = leases.acquire('key', 'sha256:' + '4' * 64, 'worker-a', now=100, ttl_seconds=10)
        completed = leases.complete(lease, 'cas:result', now=101)
        replay = leases.acquire('key', lease.fingerprint, 'worker-b', now=500, ttl_seconds=10)
        self.assertEqual(replay, completed)
        self.assertEqual(leases.complete(replay, 'cas:result', now=501), completed)
        with self.assertRaisesRegex(RecoveryError, 'conflict'):
            leases.complete(replay, 'cas:different', now=501)

    def test_coordinator_and_executor_require_durable_catalog_pairing(self):
        root, cas = self.fixture(); leases = DirectorLeaseStore(root / 'leases.sqlite'); self.addCleanup(leases.close)
        coordinator = DirectorRecoveryCoordinator(leases, ttl_seconds=17)
        self.assertEqual(coordinator.descriptor(), {
            'schema_version': 'bie.dir.durable_recovery/1.0.0', 'ttl_seconds': 17})
        catalog = SQLiteArtifactCatalog(cas, root / 'catalog.sqlite'); self.addCleanup(catalog.close)
        self.assertIsInstance(DirectorArtifactIO(catalog), DirectorArtifactIO)


if __name__ == '__main__': unittest.main()
