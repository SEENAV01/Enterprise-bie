"""Compose the native Director index with the existing producer run/CAS.

The pipeline SQLitePersistence remains the sole run/stage authority. The native
Director catalog, leases, idempotency and revision tables are stage-internal
indexes in that same governed run directory; every payload uses the supplied
canonical CAS. No envelope is reconstructed or republished during import.
"""
from contextlib import contextmanager
from dataclasses import asdict
import stat
import threading
from types import SimpleNamespace

from bie.infrastructure.artifact_store import ArtifactRecord, BlobRef
from bie.infrastructure.idempotency_store import SQLiteIdempotencyStore
from bie.infrastructure.persistence import PersistedArtifactRecord
from bie.director.director_artifacts import (
    DirectorArtifactIO, envelope_from_dict, canonical as native_canonical,
)
from bie.director.director_durable_recovery import (
    SQLiteArtifactCatalog, DirectorLeaseStore, DirectorRecoveryCoordinator,
)
from bie.director.production_adoption import DirectorProductionAssembly
from .contracts import require, strict_json
from .durable_slice import ClosedPersistence
from .pedagogy_codec import ProducerArtifactCatalog


INDEX_VERSION = "director-production-v1"
MAX_NATIVE_RECORDS = 1000


class DirectorReadPersistence(ClosedPersistence):
    """Own one artifact-read connection; inherit every canonical SQL operation.

    Only load_artifact uses the owned connection. Writes and all other reads
    retain the historical fresh-connection adapter, including operation-local
    total_changes behavior. No artifact rows or CAS bytes are cached.
    """

    def __init__(self, path):
        self._read_connection = None
        self._read_identity = None
        self._reading_artifact = False
        self._read_context_active = False
        self._read_owner = None
        self._read_closed = False
        try:
            super().__init__(path)
        except BaseException:
            self.close()
            raise

    def _path_identity(self):
        try:
            current = self.path.lstat()
        except OSError:
            require(False, "producer_persistence_path_invalid")
        require(stat.S_ISREG(current.st_mode) and not stat.S_ISLNK(current.st_mode),
                "producer_persistence_path_invalid")
        return current.st_dev, current.st_ino

    def load_artifact(self, artifact_id):
        with self._lock:
            require(not self._read_closed, "producer_persistence_closed")
            require(not self._reading_artifact and not self._read_context_active,
                    "producer_persistence_reentrant_read")
            self._reading_artifact = True
            self._read_owner = threading.get_ident()
            try:
                return super().load_artifact(artifact_id)
            finally:
                self._reading_artifact = False
                self._read_owner = None

    @contextmanager
    def _conn(self):
        if not self._reading_artifact or self._read_owner != threading.get_ident():
            # The original canonical ownership wrapper remains authoritative
            # for initialization, mutations, run state and other read methods.
            with super()._conn() as connection:
                yield connection
            return
        with self._lock:
            require(not self._read_closed, "producer_persistence_closed")
            require(not self._read_context_active,
                    "producer_persistence_reentrant_read")
            identity = self._path_identity()
            if self._read_connection is None:
                # Use the exact canonical connector/pragmas/autocommit policy.
                from bie.infrastructure.persistence import SQLitePersistence
                connection = SQLitePersistence._conn(self)
                try:
                    require(self._path_identity() == identity,
                            "producer_persistence_path_changed")
                except BaseException:
                    connection.close()
                    raise
                self._read_connection = connection
                self._read_identity = identity
            require(identity == self._read_identity,
                    "producer_persistence_path_changed")
            require(not self._read_connection.in_transaction,
                    "producer_persistence_transaction_active")
            self._read_context_active = True
            try:
                # Preserve the canonical context-manager commit/rollback scope;
                # never leave a read snapshot open between method invocations.
                with self._read_connection:
                    yield self._read_connection
            finally:
                self._read_context_active = False

    def close(self):
        lock = getattr(self, "_lock", None)
        if lock is None:
            self._read_closed = True
            return
        with lock:
            require(not self._reading_artifact and not self._read_context_active,
                    "producer_persistence_reentrant_read")
            self._read_closed = True
            if self._read_connection is not None:
                self._read_connection.close()
                self._read_connection = None
            self._read_identity = None


def native_record(service, run_id, row):
    """Recover native ordered parents, which the outer SQL parent set sorts.

Native output catalog metadata is retained as index metadata, not inserted into
the immutable ArtifactEnvelope. Existing Task032 rows need no schema mutation.
    """
    require(row.run_id == run_id and
            row.metadata.get("producer_codec") == "director-input-v1",
            "foreign_director_artifact")
    blob = BlobRef(row.blob_algorithm, row.blob_digest, row.blob_size)
    envelope = envelope_from_dict(strict_json(service.cas.get_bytes(blob)))
    parents = [ref.artifact_id for ref in envelope.parent_refs]
    require(envelope.artifact_id == row.artifact_id and
            envelope.artifact_type == row.artifact_type and
            envelope.run_id == run_id and
            set(parents) == set(row.parent_artifact_ids) and
            len(parents) == len(row.parent_artifact_ids),
            "director_codec_index_mismatch")
    metadata = row.metadata
    if metadata.get("director_native_index") == INDEX_VERSION:
        require(metadata.get("director_native_parent_order") == parents and
                type(metadata.get("director_native_metadata")) is dict,
                "director_native_index_mismatch")
        metadata = metadata["director_native_metadata"]
    require(metadata.get("content_hash") == envelope.content_hash,
            "director_native_index_mismatch")
    return ArtifactRecord(row.artifact_id, row.artifact_type, blob, run_id,
                          row.stage_id, parents, row.evidence, metadata)


class OrderedProducerArtifactCatalog(ProducerArtifactCatalog):
    """Task033 input codec retains native envelope order across SQL reload.

The older codec remains the default for historical profiles. This explicit
composition hook changes only the Task033 index representation, never payloads,
artifact identity or the producer's immutable historical stage scopes.
    """

    def convert(self, row):
        return native_record(self.service, self.run_id, row)


class GuardedDirectorCatalog(SQLiteArtifactCatalog):
    """Native durable index; publication is guarded by the outer worker fence."""

    def __init__(self, service, run_id):
        self.service, self.run_id = service, run_id
        self.importing = False
        # Do not reuse runs.sqlite3: its artifact_records table is a different
        # canonical schema. This is the Director's existing stage-only index.
        try:
            super().__init__(service.cas, service.root / "director-catalog.sqlite3")
            require(len(self.records) <= MAX_NATIVE_RECORDS, "director_codec_budget")
            require(all(record.run_id == run_id for record in self.records.values()),
                    "foreign_director_artifact")
            self.sync_outer()
            require(not self.verify_durable_index(), "director_native_index_mismatch")
        except BaseException:
            # Native hydration can fail while opening a tampered journal. Close
            # any connection already acquired before propagating the blocker.
            if getattr(self, "db", None) is not None:
                self.close()
            raise

    def sync_outer(self):
        """Index exact verified Task032 ancestry using its original CAS bytes."""
        pending = {}
        for artifact_id in self.service.persistence.artifacts_for_run(self.run_id):
            row = self.service.persistence.load_artifact(artifact_id)
            if row.metadata.get("producer_codec") == "director-input-v1":
                pending[artifact_id] = native_record(self.service, self.run_id, row)
        require(len(pending) <= MAX_NATIVE_RECORDS, "director_codec_budget")
        self.importing = True
        try:
            while pending:
                ready = [aid for aid, record in pending.items()
                         if set(record.parent_artifact_ids) <= self.records.keys()]
                require(ready, "director_codec_ancestry")
                for aid in sorted(ready):
                    record = pending.pop(aid)
                    if aid in self.records:
                        require(self.get_record(aid) == record,
                                "director_native_index_mismatch")
                    else:
                        self.register(record)
        finally:
            self.importing = False

    def get_record(self, artifact_id):
        self.service.authorize()
        record = super().get_record(artifact_id)
        require(record.run_id == self.run_id, "foreign_director_artifact")
        saved = self.db.execute(
            "SELECT record_json FROM artifact_records WHERE artifact_id=?",
            (artifact_id,)).fetchone()
        require(saved is not None and saved[0] == native_canonical(asdict(record)),
                "director_native_index_mismatch")
        # This is an index lookup, not a content load. DirectorArtifactIO.load
        # always calls read_artifact -> CAS.get_bytes (length/digest check) and
        # validates the native envelope/reference. Reading CAS here would add
        # two redundant full reads per native load without stronger admission.
        return record

    def register(self, record):
        self.service.write_guard()
        require(record.run_id == self.run_id, "foreign_director_artifact")
        require(len(self.records) < MAX_NATIVE_RECORDS or
                record.artifact_id in self.records, "director_codec_budget")
        envelope = envelope_from_dict(strict_json(self.cas.get_bytes(record.blob)))
        require(envelope.artifact_id == record.artifact_id and
                envelope.artifact_type == record.artifact_type and
                envelope.run_id == self.run_id and
                [ref.artifact_id for ref in envelope.parent_refs] == record.parent_artifact_ids and
                record.metadata.get("content_hash") == envelope.content_hash,
                "director_native_index_mismatch")
        if not self.importing:
            self.service.fault("after_DIRECTOR_native_" + record.artifact_type + "_cas")
            self.service.fault("after_DIRECTOR_native_cas")
        self.service.write_guard()
        super().register(record)
        if not self.importing:
            self.service.fault("after_DIRECTOR_native_" + record.artifact_type + "_index")
            self.service.fault("after_DIRECTOR_native_index")
        self.service.write_guard()


@contextmanager
def native_runtime(service, run_id, stack, policy=None, semantic_policy=None):
    """Yield the actual hardened production assembly and close owned handles.

The outer producer holds its own SQLite lease transaction during execution.
Native Director state therefore uses a distinct stage-internal SQLite file, not
the outer idempotency file; sharing that file would lock/nest transactions.
    """
    catalog = GuardedDirectorCatalog(service, run_id)
    idempotency = leases = None
    try:
        path = service.root / "director-state.sqlite3"
        idempotency = SQLiteIdempotencyStore(str(path))
        leases = DirectorLeaseStore(path)
        recovery = DirectorRecoveryCoordinator(leases)
        io = DirectorArtifactIO(catalog)
        if stack is None:
            # Reopening a committed native result validates artifacts/revisions
            # without constructing providers or invoking model execution.
            assembly = SimpleNamespace(io=io, idempotency=idempotency,
                                       recovery=recovery)
        else:
            assembly = DirectorProductionAssembly(
                io, idempotency, recovery,
                stack.generator, stack.generator_identity,
                stack.critic, stack.critic_identity, stack.annotations,
                policy=policy, semantic_policy=semantic_policy)
        yield assembly
    finally:
        if leases is not None:
            leases.close()
        if idempotency is not None:
            idempotency.close()
        catalog.close()


def import_native_result(service, run_id, catalog, refs):
    """Bridge exact native ArtifactRecords to the authoritative outer index.

This imports the native envelope identity, original CAS blob and native parent
order. It creates no alias artifact and makes no cross-store atomicity claim.
Explicit recovery can finish an interrupted index bridge idempotently.
    """
    require(isinstance(catalog, GuardedDirectorCatalog) and
            catalog.service is service and catalog.run_id == run_id,
            "foreign_director_artifact")
    io = DirectorArtifactIO(catalog)
    selected = tuple(io.load(ref).to_ref() for ref in refs)
    graph = io.load_graph(selected)
    pending = {aid: catalog.get_record(aid) for aid in graph}
    known = set(service.persistence.artifacts_for_run(run_id))
    while pending:
        ready = [aid for aid, record in pending.items()
                 if set(record.parent_artifact_ids) <= known]
        require(ready, "director_codec_ancestry")
        for aid in sorted(ready):
            record = pending.pop(aid)
            service.write_guard()
            if aid in known:
                existing = native_record(service, run_id,
                                         service.persistence.load_artifact(aid))
                require(existing == record, "director_native_index_mismatch")
            else:
                metadata = dict(record.metadata, privacy="PRIVATE",
                    producer_codec="director-input-v1", profile=service.profile,
                    director_native_index=INDEX_VERSION,
                    director_native_parent_order=record.parent_artifact_ids,
                    director_native_metadata=record.metadata)
                durable = PersistedArtifactRecord(record.artifact_id,
                    record.artifact_type, record.blob.algorithm, record.blob.digest,
                    record.blob.size, run_id, record.stage_id, record.evidence,
                    metadata, record.parent_artifact_ids)
                service.persistence.register_artifact(durable)
                require(native_record(service, run_id,
                    service.persistence.load_artifact(aid)) == record,
                    "director_native_index_mismatch")
            known.add(aid)
            service.fault("after_DIRECTOR_native_bridge")
    return selected
