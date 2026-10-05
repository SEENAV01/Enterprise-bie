# BIE-PROD-029 — governed source-grounded DI → Knowledge slice

New explicit productization continuation decision after canonical Task028, not
an interpretation of historical internal atomic 029 identifiers. Base:
`c9f8725d1b2359b560dc9422f07ef702001edef8`; tree:
`c0661eb7903a1a82e769ee2b567ec59a1497005c`.

## Ownership and executable boundary

`bie/productization/` composes existing native DI, KI, infrastructure orchestration,
run state, SQLitePersistence, SQLiteDurableTaskQueue, SQLiteIdempotencyStore and
the already admitted budgeted FileSystemCAS. Canonical engines are unchanged.
The existing DirectorLeaseStore supplies fenced durable lease machinery without
executing Director or changing its source. Its table is reused in the canonical
per-run idempotency database; no new queue/store/CAS implementation exists.

SOURCE → DOCUMENT_INTELLIGENCE → KNOWLEDGE are the only executed stages.
The private artifact contracts are `bie.document.structured/1` and
`bie.knowledge.graph/1`, implemented/validated in `contracts.py` and `candidates.py`.
Full source text lives only in private CAS document/candidate/graph payloads.
Source anchors/page map/reading order/geometry are serialized from canonical DI,
not reconstructed from safe counts. Safe status/evidence has no source text.

The trusted Python `KnowledgeProducerControlPlane` requires an authenticated
Section18 principal, explicit profile enablement, worker/create permissions,
tenant-bound admitted source and canonical CAS integrity. It delegates native
execution; it does not duplicate an operator engine. `native_pdf_inspection_v1`,
its HTTP admission/controls/CLI, Task028 APIs/workers and Android are unchanged.
The distinct `source_grounded_di_knowledge_v1` port is NOT added to the existing
inspection HTTP option parser. Android/HTTP product-run integration is later work.
In-flight producer pause/cancel is unsupported and fails closed, never pretended.
Its dedicated bounded child is `apps/operator/knowledge_worker_child.py`; it is
not the Task028 service or the existing Section18 inspection worker. The
existing local PDF process budget is reused unchanged (1 GiB, 30 CPU seconds,
45 wall seconds), and is a resource boundary, NOT a network/code sandbox.

## Technical candidate profile, not academic acceptance

The existing provider-neutral gateway registry/request/response interfaces are
reused. The installed `technical_source_derived` / `lexical-extractive-v1` adapter
reads actual native PDF text. Bounded lexical candidates and verbatim claims vary
with source content; no authored concepts or manufactured relation connectivity
are supplied. Canonical KI graph and E2E validators assemble/check the result.
The profile is explicitly TECHNICAL_SOURCE_DERIVED; lexical tokens are not proof
of educational concepts or semantic/academic correctness. Optional unsupported
semantic structures are rejected rather than asserted. Claims require exact
source substrings and valid anchors; no paraphrase correctness is claimed.
Admission is bounded to 25 MiB PDF input; the extracted private contract is
bounded to 500 pages, 200 blocks, 512 KiB text and 4 MiB serialized artifacts.
Excess fails closed. Whole-book streaming/chunked semantic processing is not
claimed by this deliberately bounded composition slice.

There is no live API transport, secret lookup or paid call in this task. Unavailable
provider/model selections persist BLOCKED knowledge state and safe evidence,
never an empty successful graph. Live semantic candidate generation and independent
assessment require a separately configured/protected validation decision.

## Durable admission, fencing and recovery

An existing admitted source CAS blob is promoted by verified digest/length and a
new producer-run source record; bytes are not copied to a second CAS. Per-run
namespaces use the existing canonical SQLite schemas. Run identity is tenant/key/
profile bound; canonical idempotency fingerprints include source, privacy, schemas,
provider/model and prompt policy. Conflict fails closed. Stochastic output is not
claimed deterministic; new intent requires a new key/revision.

The durable resolver reads canonical persisted attempts and verifies CAS outputs.
Every transition is persisted. ACK follows verified artifact/evidence and terminal
state, not computation alone. Only the dedicated producer capability is polled.
There is no automatic retry/redrive or distributed atomicity claim. Fenced lease
transactions serialize commit authority; stale writes are rejected. CAS/state/queue
remain separate stores, with explicit interrupted-attempt recovery after lease
expiry. A recovery preserves FAILED parent attempts and creates a new immutable
attempt, or verifies terminal output before reconciling an unacknowledged delivery.
Seeded-expiry unit controls are labelled as such; real process smoke independently
proves native extraction, genuine child execution, all ACKs and reopen/replay.

Private text retention is explicitly LOCAL_PROCESSING_ONLY / PRIVATE_LOCAL_CAS.
It adds no reuse/training/export rights and claims no encryption at rest.

## Verification and non-claims

Run `tools/run_task029_tests.py --lane new --output <receipt>` and the `affected`
lane, then `scripts/smoke_bie_di_knowledge.py --output <receipt>`. Safe runners do
not upload raw tracebacks/private payloads. CI is credential-free Ubuntu 24.04,
Python 3.13.5, pinned approved actions and unchanged API/DI dependencies.

The default enterprise graph does not explicitly enumerate Math or Audio nodes.
This task does not repair the full graph or bypass their future dependency work.
All later stages remain NOT_RUN. No prerequisite/reasoning/lesson/director/audio/
video/game/QA-release execution, academic accuracy, learner improvement, real-book
product acceptance, public deployment or enterprise security acceptance is claimed.
No PR/merge/Task030 is authorized by this implementation pass.

Local focused verification: 79 distinct new Task029 methods and 490 affected
inherited methods passed with zero failures/errors/skips (569 unique methods;
reruns are not counted). The real bounded Windows child executed all three
stages, persisted graph/evidence, ACKed all three tasks and verified fresh
reopen/replay. This is synthetic/native technical evidence, not a live-model
or academic-quality gate. On Windows the existing Section18 GC-before-teardown
harness policy is reused without modifying inherited source/assertions. Full
Linux native/canonical preservation remains the existing hosted gate's authority.
Producer admission/work/recovery reserves the existing catalogue audit capacity
before native effects, inside the canonical catalogue transaction. Exhaustion
blocks before native work. This is not a cross-store atomicity guarantee.

The unchanged required integrated gate was also attempted locally. Lossless
archive/source preservation, canonical integrity, ingested-archive integrity and
Section17 adoption passed. The broader Windows enterprise run was NOT green:
7,342 tests, 142 failures, 405 errors, 5 skips. Its first native GAME failures
include unavailable POSIX `resource` imports; this does not establish the exact
cause of every other failure. No canonical assertion, dependency, sandbox or
engine was changed to green that platform-incompatible lane. The subsequent
complete Section17 execution gate was not reached. Full approved Linux canonical
preservation is still required before any integration PR/merge.
