"""BIE-DIR-HARD-REPAIR-001: durable current lesson revision in existing SQLite.

Immutable CAS artifacts stay available for audit. Currentness is checked at every
consumer read. No previous revision becomes current again after a failed repair.
This does not recover a lost ArtifactCatalog index or a distributed worker lease.
"""
from contextlib import contextmanager
from dataclasses import dataclass
from .contract_validation import nonblank
from .director_artifacts import canonical, parse_json
from bie.infrastructure.idempotency_store import SQLiteIdempotencyStore


class RevisionError(ValueError):
    pass


@dataclass(frozen=True)
class DirectorRevision:
    run_id: str
    lesson_id: str
    attempt: int
    execution_fingerprint: str
    owner: str
    state: str
    artifact_id: str | None
    inputs_json: str
    invalidated_inputs_json: str


class DirectorRevisionStore:
    def __init__(self, store):
        if not isinstance(store, SQLiteIdempotencyStore):
            raise ValueError('existing SQLite idempotency store required')
        self.db = store.db
        self.db.execute('''CREATE TABLE IF NOT EXISTS director_revisions(
            run_id TEXT NOT NULL, lesson_id TEXT NOT NULL, attempt INTEGER NOT NULL,
            execution_fingerprint TEXT NOT NULL, owner TEXT NOT NULL, state TEXT NOT NULL,
            artifact_id TEXT, inputs_json TEXT NOT NULL, invalidated_inputs_json TEXT NOT NULL,
            PRIMARY KEY(run_id,lesson_id))''')
        self.db.commit()

    def get(self, run_id, lesson_id):
        row = self.db.execute('SELECT * FROM director_revisions WHERE run_id=? AND lesson_id=?',
                              (run_id, lesson_id)).fetchone()
        return DirectorRevision(*row) if row else None

    def begin(self, run_id, lesson_id, attempt, execution_fingerprint, owner, input_artifact_ids, ancestor_ids=None):
        for value in (run_id, lesson_id, execution_fingerprint, owner):
            nonblank(value, 'revision identity')
        if type(attempt) is not int or not 1 <= attempt <= 3:
            raise RevisionError('bounded stage attempt required')
        if not input_artifact_ids:
            raise RevisionError('actual input artifact IDs required')
        for artifact_id in input_artifact_ids: nonblank(artifact_id, 'input artifact ID')
        with self.db:
            self.db.execute('BEGIN IMMEDIATE')
            prior = self.get(run_id, lesson_id)
            if prior and attempt != prior.attempt + 1:
                raise RevisionError('new revision requires the next bounded attempt')
            if prior and prior.state == 'STALE':
                if ancestor_ids is None or set(parse_json(prior.invalidated_inputs_json)) & set(ancestor_ids):
                    raise RevisionError('superseded input ancestors must be replaced before retry')
            self.db.execute('INSERT OR REPLACE INTO director_revisions VALUES(?,?,?,?,?,?,?,?,?)',
                (run_id, lesson_id, attempt, execution_fingerprint, owner, 'RUNNING', None, canonical(list(input_artifact_ids)), '[]'))
        return self.get(run_id, lesson_id), prior

    def _owned(self, revision):
        current = self.get(revision.run_id, revision.lesson_id)
        if current != revision or current.state != 'RUNNING':
            raise RevisionError('revision was superseded or is no longer running')

    def publish(self, revision, artifact_id):
        nonblank(artifact_id, 'director output')
        with self.db:
            self.db.execute('BEGIN IMMEDIATE')
            self._owned(revision)
            self.db.execute('UPDATE director_revisions SET state=?,artifact_id=? WHERE run_id=? AND lesson_id=?',
                ('READY_FOR_REVIEW', artifact_id, revision.run_id, revision.lesson_id))

    def fail(self, revision):
        with self.db:
            self.db.execute('''UPDATE director_revisions SET state='FAILED' WHERE
                run_id=? AND lesson_id=? AND execution_fingerprint=? AND owner=? AND state='RUNNING' ''',
                (revision.run_id, revision.lesson_id, revision.execution_fingerprint, revision.owner))

    def assert_current(self, artifact):
        if artifact.artifact_type != 'director.plan':
            raise RevisionError('director.plan required')
        current = self.get(artifact.run_id, artifact.payload['lesson_id'])
        if (current is None or current.state != 'READY_FOR_REVIEW' or current.artifact_id != artifact.artifact_id
                or artifact.metadata.get('execution_fingerprint') != current.execution_fingerprint):
            raise RevisionError('director revision is missing, stale, running or failed')
        return current

    @contextmanager
    def guard(self, artifact):
        """Short publication/read lock; no provider call runs inside this guard."""
        with self.db:
            self.db.execute('BEGIN IMMEDIATE')
            self.assert_current(artifact)
            yield

    def invalidate_inputs(self, io, run_id, superseded_refs, reason):
        """Invalidate only lessons whose verified ancestor graph contains an old input.

        Supply exact *old* refs when upstream source/RE/PED revisions change.
        Descendants become unusable transitively through the consumer read gate.
        """
        nonblank(reason, 'invalidation reason')
        refs = tuple(superseded_refs)
        if not refs:
            raise ValueError('exact superseded input refs required')
        old = [io.load(ref) for ref in refs]
        if any(a.run_id != run_id for a in old):
            raise ValueError('cross-run invalidation')
        old_ids = {a.artifact_id for a in old}
        receipts = []
        with self.db:
            self.db.execute('BEGIN IMMEDIATE')
            rows = self.db.execute("SELECT * FROM director_revisions WHERE run_id=? AND state IN ('READY_FOR_REVIEW','RUNNING')", (run_id,)).fetchall()
            for row in rows:
                revision = DirectorRevision(*row)
                dependencies = tuple(io.load(r).to_ref() for r in parse_json(revision.inputs_json))
                graph = io.load_graph(dependencies)
                matched = sorted(old_ids & graph.keys())
                if not matched:
                    continue
                parents = (io.load(revision.artifact_id).to_ref(),) if revision.artifact_id else dependencies
                receipt = io.derive('evidence.director_invalidation', run_id, parents,
                    {'schema_version': 'bie.dir.invalidation/1.0.0', 'superseded_artifact_ids': matched,
                     'reason': reason, 'execution_fingerprint': revision.execution_fingerprint,
                     'scope': 'DIRECTOR_AND_ALL_REGISTERED_CONSUMER_DESCENDANTS', 'accepted': False},
                    stage_id='DIRECTOR', metadata={'requires_review': True, 'accepted': False}, evidence=True)
                self.db.execute("UPDATE director_revisions SET state='STALE',invalidated_inputs_json=? WHERE run_id=? AND lesson_id=?",
                                (canonical(matched), run_id, revision.lesson_id))
                receipts.append(receipt)
        return tuple(receipts)
