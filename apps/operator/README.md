# Section 18 operator candidate — cumulative Batch 002

This is a new product boundary over **unchanged canonical BIE source**, not a
parallel document engine. The existing Android client and `apps/api` remain
unchanged. This is ZIP-development source, not integrated or deployed software.

## Executable scope

Original tasks: BIE-APP-RUN-001 through 008; BIE-APP-GRAPH-001 and 002.

Batch002 adds GRAPH-003, LESSON-001..005 and ART-001..004 in the same local
artifact-bound profile. Native producer execution is not fabricated. `ProductArtifacts`
has trusted Python publication ports; there is no browser publication/worker API.
Each publication is a canonical CAS blob and persisted artifact, linked to the
actual run/source and existing parent artifacts. Its immutable identity, parent
list and metadata are sealed in the existing tamper-evident product index.

- Reasoning uses canonical `ReasoningDecision` and graph validation, including
  actual dependency references, confidence, assumptions, uncertainty, alternatives
  and RESOLVED/ABSTAINED/CONFLICT/review distinctions. Rejected alternatives are
  not presented as resolved decisions. Confidence is producer-reported, not a
  semantic quality measurement or learner score.
- Curriculum checks the stored plan against the canonical book curriculum
  optimizer. Ordered units, objectives, prerequisite edges, lesson groups and
  planned review/timing are displayed, not invented measured durations.
- Lessons reuse canonical lesson architecture and pedagogy plans with section
  timing, assessments, objective coverage and source/evidence links.
- Director views validate canonical script plans and scene/narration/visual
  bindings. Timings are planned, not rendered media evidence.
- Scene IR uses the unified native codec and schema/temporal/spatial/accessibility
  validators. Element inventory, spatial boxes and frame ranges are displayed;
  arbitrary props, assets, state bindings and code are never executed. IR is
  explicitly not compiled/rendered/accepted.
- Game director plans reuse canonical validation and fingerprints. Objectives,
  mechanics, rounds, feedback, mastery targets and remediation are visible.
  A plan is explicitly not a built/playable game or measured learner improvement.
- Artifact browsing is run/tenant-scoped, filtered and paginated. Source bytes
  have no content/download endpoint. Raw metadata is not exposed.
- Lineage uses canonical `ArtifactAPI` and `ArtifactCatalog` roots/cycle checks
  over actual persisted records; all selected CAS contents are verified. Traversal
  is bounded and cap overflow is explicit, never a silently partial complete graph.
- Evidence delegates `EvidenceAPI`, identifies SYNTHETIC_TEST, validates hashes
  and shows unverified signature/reviewer state honestly. Producer labels alone
  are not attestations. Existing PDF evidence is safe-decoded; unknown types are
  metadata-only.
- Generated code is UTF-8, hash-verified, size-limited and line-paginated. It is
  literal DOM text only, never executed or compiled in the display process.
- Credential clear invalidates pending responses before they can repopulate
  private views. Local auth/tenant checks apply to every artifact endpoint.

Added GET routes: `/operator/v1/runs/{run_id}/views/{kind}`, `/artifacts`, and
`/artifacts/{artifact_id}/lineage`, `/evidence`, `/code`. Collections are capped
at 200 domain items, 2048 stored artifacts per run, 256 lineage nodes and 100
page rows. View blobs are at most 512 KiB and generated code at most 256 KiB.
Metadata-only listings do not imply content has been verified; content/lineage
reads explicitly verify it. No new external package is introduced.

- Raw PDF import is streamed to private temporary staging, capped at 25 MiB,
  inspected by canonical `inspect_real_pdf`, then stored by `FileSystemCAS`.
  One bounded in-memory pass is needed by the existing native PDF/CAS APIs;
  this is **not** a zero-copy upload claim. Client filenames never choose paths.
- Source SHA, inventory and VALID/INVALID diagnostics persist. PDF metadata,
  title strings, raw source and extracted book text are not returned.
- `RunAPI.create` is actually invoked through a product adapter. Its immutable
  `RunConfig` and child-retry lineage are persisted in canonical CAS/artifacts.
- Deterministic operator intent IDs bind tenant, key, source and config; the
  native job delegates to `PdfInspectionJobService`, `SQLitePersistence`,
  `SQLiteIdempotencyStore` and `SQLiteDurableTaskQueue`.
- Status and timeline read native persisted attempts/events and queue state.
  Operator admission controls are separately identified, never disguised as
  native engine events or percentages.
- Failure diagnostics and evidence links are safe and CAS-verified. The evidence
  reader delegates to canonical `EvidenceAPI`. Retry creates a child and preserves
  the failed parent; a retry key replays the same child.
- Queued pause holds **actual controlled-worker admission** across restart.
  Resume permits dispatch. Queued cancel dead-letters the actual canonical task,
  records BLOCKED in canonical persistence and presents product CANCELLED only
  with its native cancellation receipt. Running/terminal controls are rejected.
- The graph producer port invokes canonical KI/PR graph contracts and persists
  immutable source-bound artifacts. Viewers show SVG directed graphs, relation
  tables, roots/teaching order, linked source validation and provenance. Missing
  graphs show NOT_RUN. Producer labels do not establish semantic truth.

## Run locally

Install from this extracted source with the existing pinned extras:

```
python -m pip install -e ".[document-intelligence,document-intelligence-layout,api,api-test]"
python -m pip check
python -X utf8 scripts/run_bie_operator.py --data-root <private-new-directory> --port 8080
```

Provision `BIE_OPERATOR_TOKEN` only in the process environment with a strong
random credential of at least 32 ASCII non-whitespace characters. No credential
is included in this package. The runner binds **127.0.0.1 only**. Enter the
credential in the local page; it is never saved in browser storage or sent in a
URL. A separate short-lived, package-only preview grant is used for sandboxed
game resources; it cannot authorize any operator API. Access logging is disabled
and Referrer-Policy is no-referrer. Default runner permission scope is a single local operator. The application
factory supports separately granted expiring tenant-scoped principals with
read/source/create/control/retry/publish/worker permissions and live revocation.

After creating a run, an authorized local operator can execute exactly one job:

```
python scripts/run_bie_operator_worker.py --data-root <same-private-directory> --run-id <run-id>
```

**Do not run the old unguarded PDF-worker CLI against these per-run namespaces.**
The operator controls govern the new controlled executor, not arbitrary processes
running under the same OS user. There is no browser/Android worker-launch API.
HTTP source/run/control/graph endpoints live under `/operator/v1/`. Existing
canonical `/v1/jobs` contracts are not replaced or remapped.

## Explicit limitations

The executable profile is `native_pdf_inspection_v1`. Requested video/game
outputs in canonical config are NOT_RUN: a genuine full learning producer is not
bound. This does not fabricate book-derived concept/prerequisite graphs. Real
Money inspection has no real KI/PR graph execution evidence. Synthetic native
graph tests are labelled SYNTHETIC_TEST, not real-book acceptance.

Local authorization is not enterprise SSO, public IAM, TLS, encryption at rest,
or production tenant isolation. No public bind/deployment is offered. CSRF is
bounded by bearer-only auth, same-origin write checks and no CORS allowance.
Private storage administrators can bypass local permissions or rewrite local
hash chains; external audit notarization is not claimed.

The catalog serializes local admission/dispatch with SQLite, not a distributed
transaction. Parser time/memory isolation, crash-window reconciliation and
broader privileged-operator audit review remain explicit final hardening lanes.
A dead/interrupted worker is not silently retried. Cancellation does not kill
already running processes. Backend unavailable/tampered/inconsistent state fails
closed rather than becoming a fake success.

Phone/tablet evidence is actual browser viewport/AX testing, **not** Android
physical-device acceptance. Task 028 remains paused. Sections 1–17, legacy
release CONTRACT_ONLY semantics and global continuation are preserved.

## Verification

```
python -B tools/run_section18_tests.py --lane atomic --output <receipt-directory>
python -B tools/run_section18_tests.py --lane regression --output <receipt-directory>
python -B tools/run_section18_tests.py --lane browser --output <receipt-directory>
python -B tools/section18_mutation_controls.py <receipt.json>
```

Browser tests require Node 22 and a native Edge/Chromium executable selected with
`BIE_SECTION18_BROWSER`; the Windows default is installed Microsoft Edge. They
use an isolated temporary profile, keep browser sandboxing enabled, connect only
to loopback and close all test processes. Missing browser tooling is an explicit
failure, never a skipped test or synthetic replacement. Each atomic task selects
only its declared test methods; inherited helpers/reruns/mutations add no counts.

## Batch003 checkpoint A — render and compiled-game previews

`GET /operator/v1/runs/{run_id}/previews/render` and `/previews/game`
show actual bound artifacts or `NOT_RUN`. Scene IR and Game IR are not media.
Only a trusted Python producer can publish; there is no HTTP publisher.

Render publication validates a full `RenderReceipt`, source identity, exact
artifact hash/size, input/policy binding and native `video_v2.inspect_bytes`.
Required frame inventory, dimensions, codec, pixel format, clocks and audio are
checked against the receipt. `GET .../render/media` serves verified MP4 bytes,
single ranges (206), strong ETag/If-Range, bounded suffix/open ranges and safe
416 responses. HEAD returns metadata without a body. Media is capped at25 MiB;
larger future render artifacts require a separately governed streaming design.
No automatic playback or QA/release PASS is invented.

Game publication delegates to native compiler-binding, package/self-manifest
and module-graph verification. Package inventory, source binding, file/total
caps, physical paths, assets and the exact native entrypoint are checked.
There is no Game IR-to-playable shortcut and no untrusted code execution in
the operator display process. `POST .../game/preview-grant` issues a maximum
120-second default grant (configured maximum300), scoped to that immutable
package and that exact credential grant. It expires, is invalid after service
restart or bearer revocation, and can be explicitly stopped/revoked. Each
resource revalidates authorization, record seals, parent CAS and package hashes.

The iframe uses `sandbox="allow-scripts"`, never `allow-same-origin`, popups,
forms, downloads or parent-navigation permission. HTTP CSP repeats the sandbox,
permits only this grant's resource prefix, and prohibits connect/worker/object
access. Opaque-origin ES modules get `Access-Control-Allow-Origin: null` only
on the expiring package resource route. Operator APIs have no CORS allowance.
Grants do not confer API privileges. The UI clears frames, timers and blob URLs
on credential/run changes; any already delivered bytes cannot be unlearned.

Previewing an actual compiled package is not a signed Linux browser witness,
learning-quality QA, rights approval, release authorization or product acceptance.
QA remains REVIEW_REQUIRED. Fixture origin stays SYNTHETIC_TEST, even when a
real native compiler, tsc, React runtime and browser execute the fixture.

The synthetic fixture builder is test-only, requires pinned TypeScript5.9.3 and
explicit UTF-8 mode, and produces no canonical Linux build/sandbox receipt.
The embedded MP4 is a hash-pinned Section16 diagnostic, not a Remotion learning
render. Official native render/game execution continues to require the existing
Linux sandbox/toolchain; the Windows application does not bypass that gate.
Run commands/tests with `python -X utf8` on Windows for canonical Unicode game
source. Native vendor bytes are recovered exactly from the pinned Git blobs to
avoid Windows CRLF conversion invalidating native hash pins; no validator or
canonical checkout is changed.

HTTP range semantics reference: https://www.rfc-editor.org/rfc/rfc9110.html#section-14
Iframe isolation reference: https://html.spec.whatwg.org/multipage/iframe-embed-object.html#attr-iframe-sandbox

Remaining Batch003 tasks are QA001..004 and ADMIN001..004. Section18 is not
complete or integrated; Task028 remains PAUSED.
# Batch003 checkpoint B: evaluation/release window

Read-only `GET /operator/v1/runs/{run_id}/quality/benchmark` and
`.../quality/release` expose bounded, scoped, hash-verified historical snapshots.
There is no HTTP score publisher, evaluator dispatcher or release action.

Trusted Python adapters `Quality.bind_benchmark` and `Quality.bind_release` read
the canonical Section17 `AttemptLedger.get_report` / `ReleaseLedger.get` directly.
They bind the candidate to an actual artifact hash and the original native run,
pin dataset/manifest/policy identity, and retain failed attempts across restart.
Snapshots have immutable CAS content, artifact parents, record seals and audit
events. They do not replace the underlying evaluator or promote historical
decisions to current deployment authority.

Benchmark case decisions, missing denominator entries, version, coverage and
reference limitations are shown without answers or source excerpts. A stored
attempt ledger does not by itself attest actual BIE/provider execution. Release
metrics, critical/domain floors, configured raters, agreement and blockers come
from native receipts; diagnostic pass is not production acceptance. Missing
native receipts are NOT_RUN, not substituted with diagnostic fixture values.

Default page size10, maximum100; maximum128 snapshots/run and256KiB/snapshot.
The complete33-task implementation/security audit remains pending. Local bearer
access is not enterprise IAM; CAS/record hashes do not defend a privileged owner
able to rewrite the complete store. Task028 remains paused.

# Batch003 checkpoint C: gate and repair-history adapters

`GET /operator/v1/runs/{run_id}/assurance/gates` shows all28 canonical
`enterprise_policy()` floors and actual `ReleaseEvaluator.evaluate` results.
It requires a real persisted source/video/game candidate bound to the native run.
Missing product outputs remain NOT_RUN; they are never synthesized for a book.
No HTTP publisher, repair executor or release-control endpoint was introduced.
Every candidate parent is content-verified on publication and retrieval.

`.../assurance/repairs` reads historical attempts only through an exact canonical
`Journal.export` integrity check, pinned snapshot/policy/plan and matching attempt
receipt hashes. Failed attempts, remaining defects, before/after identity,
invalidated evidence and fresh regression outcomes remain distinct. Pending
reservations require manual review; STAGED_FOR_REVIEW never means released.

Windows gate evaluation retains SECURE_ARTIFACT_IO_UNSUPPORTED and BLOCKED.
Canonical repair execution/journal needs supported POSIX and is NOT_RUN here.
QA003 projection tests are authored local unit specimens, not native execution.
`tests/section18/test_posix_assurance.py` contains the separate mandatory native
worker/journal integration lane. QA003 stays pending until that lane passes;
its ZIP is an implementation checkpoint, not a completed task receipt.

Gate/repair UI uses structured tables and literal text, bounded pages, accessible
labels, lineage navigation and stale-response/credential-clear protection.
Historical trust expiry is displayed as evaluated, not re-certified as current.
All33-task hardening, privileged-store trust and Linux gates remain outstanding.

# Batch003 checkpoint D: actual local control plane

ADMIN001 reuses the canonical ProviderRegistry and capability/availability
contracts. Trusted Python provisioning requires a real adapter object and an
optional opaque `secretref-<64hex>` reference, never a secret value. The HTTP UI
can read tenant configuration/history and enable/disable an already registered
model with a revision pin and idempotency key. No HTTP adapter loader, credential
reader, live probe or provider invocation exists. After process restart approved
metadata survives; adapters must be rebound by the trusted host. Health remains
NOT_RUN until an actual explicit observation. Synthetic observations retain
SYNTHETIC_TEST origin; stale/binding-mismatched observations do not prove health.
Maximum128 configurations/tenant,256 immutable versions/configuration.

ADMIN002 shows actual persisted controlled-worker dispatch/completion records,
canonical WorkerHeartbeat/WorkerCapabilities validation and lease-owned work.
Heartbeat is START_AND_COMPLETION_ONLY. STALE is UNVERIFIED_STALE, not DEAD.
Hardware capacity is declared for this one-job profile, not measured. No remote
worker launch/control API is exposed. Records survive worker/service restart.

ADMIN003 reads the actual canonical per-run SQLite queue; GET never polls or
calls mutating stats/recover_expired. Tenant-owned PDF namespace scope, state
filters, lexical cursors and bounded scanning are explicit. Expired leases are
REVIEW_REQUIRED. Queue identity, counters and timestamp/state combinations are
validated; unknown diagnostics are hashed/redacted, not echoed.

ADMIN004 shows canonical dead-letter events and safe reasons. Recovery creates
a governed child retry; it does not redrive a terminal FAILED PDF parent or
alter its historical queue. Parent revision/queue digest are rechecked inside
creation, child lineage and idempotent audit are preserved. A replay returns the
child's actual current status, never an invented READY. No worker is dispatched
by recovery. Cancelled/interrupted states require review rather than fake repair.

Endpoints: `/operator/v1/admin/providers`, `.../providers/{id}/history`,
POST `.../providers/{id}/enabled`, `.../workers`, `.../queue`,
`.../dead-letters/{run_id}`, POST `.../dead-letters/{run_id}/retry`.
Permissions: admin_read, admin_config, admin_recover plus underlying read/create/
retry permissions. Cursors/max50 items, max256 scanned queue runs per page.
Provider/live-health/worker provisioning is a trusted Python port only. Browser
tables/actions are backed by those persisted routes, literal rendering and
credential-clear/delayed-response protection. No fake aggregate pool statistics.

Local bearer authorization and hash-chained catalog are not enterprise SSO,
distributed atomicity, externally notarized audit or production secret-manager
integration. Final33 audit, crash reconciliation, native QA003/POSIX execution,
cross-process quotas and deployment/real-product acceptance remain open. Task028
stays PAUSED; no GitHub integration begins at this checkpoint.

### Same-intent creation admission (finding-derived H1-001)

Overlapping exact run-creation intents share one real committed native creation
within this process and private root; different source/config/tenant/parent
preconditions never coalesce. Across Service objects for one root the coordinator
is shared. There is no historical result cache, automatic retry or new queue.
At most 32 owners and 64 waiters; followers wait at most 10 seconds and recheck
authorization before any response. Timeout/full return safe HTTP503 and do not
cancel the owner or pretend the native job failed. Failures fan out only stable
codes, never another thread's exception detail. SQLite's one-second busy timeout,
durable idempotency and cross-process conflict handling are unchanged. This does
not claim distributed contention resolution or crash atomicity.

## Batch004 — versioned configuration and attributable audit

ADMIN005 uses canonical `policy_chain` and `RunConfig`, not a new engine-policy
interpreter. Immutable versions support strict revision CAS, idempotent save,
field differences and hash-pinned activation. The supported execution policy is
offline-only native inspection, deterministic en/hi locale and bounded source
admission size. Unbound live policies/feature flags are rejected. A browser can
explicitly bind an active policy to a **new** run. The canonical config/CAS pins
policy ID, revision and SHA; the actual create path enforces locale and size.
This limit is run admission, not a retroactive global upload-policy rewrite.
Existing unbound runs keep fixed inspection defaults. Existing bound runs replay
their original immutable policy even after a new activation; new work must use
an active version. Bound child retries retain policy lineage and fail closed if
that policy is no longer active. Nothing enables a missing learning producer.

ADMIN006 stores bounded candidate-specific native Section17 manifest + policy
snapshots. Actual native aggregation, threshold, floor and domain validators run
before save. Dataset/benchmark version, complete case/metric roster, raters,
critical/domain floors and pins are displayed without answers or score claims.
Raw imported JSON goes to the server's strict duplicate-key validator rather
than being silently normalized in the browser. Trusted `execute_benchmark`
delegates to an actual `ReleaseLedger`; no HTTP evaluator, runner-registration
or score-publication port exists. Native frozen-campaign invariants prevent
silent edits to earlier decisions. Missing raters/attestations remain BLOCKED,
authored fixture measurements remain diagnostic, and release authorization stays
false. Config activation is NOT evaluator execution or acceptance.

ADMIN007 verifies the durable catalogue chain and a canonical `AuditLog` safe
projection. Sequence, actor, action, resource, timestamp, before/after hashes,
authorization result and receipt digest are visible; raw details are not. New
configuration events have explicit tenant binding. Older events are shown only
when ownership can be uniquely proven from their exact resource, never inferred
from actor names. Ambiguous/unowned events are omitted fail-closed; their counts
are not leaked to another tenant. Historical authorization may truthfully be
LEGACY_NOT_RECORDED. The in-memory canonical projection is not substituted for
durability or claimed as an external signature. No HTTP audit mutation exists.

Routes: GET `/operator/v1/governance/{policy|benchmark}`, POST
`.../{id}/versions`, GET `.../{id}/history`, GET `.../{id}/diff`, POST
`.../{id}/activate`, GET `/operator/v1/admin/audit`. Read needs admin_read;
mutation additionally needs admin_config; actual creation needs create. Known
admin readers denied config writes get safe DENY audit events without payloads
or keys. Revoked/expired identities cannot write. Maximum128 configs/kind/tenant,
256 versions/config, 50 page rows, 256 audit rows scanned/page and 65,536 events
for new governance writes. Existing audit verification remains proportional to
the whole bounded local chain; production-scale indexing/anchoring is not claimed.

Structured browser tables, editable policy fields, frozen benchmark import,
history/diff/activation and explicit next-run binding are executable. Credential
clear removes forms, selected policy, private tables and delayed responses.
Phone/tablet browser testing does not replace Android-device acceptance.

QA003 supported-POSIX native execution, all33 completeness/security audit,
finding-driven hardening/re-audit and the final COMPLETE master remain required.
Task028 is PAUSED. No GitHub integration, deployment or product acceptance.
## H1-002 — bounded catalogue and worker receipt credits

Every operator catalogue producer now passes the same central admission and
complete integrity checks. Local defaults: 65,536 audit events, 32,768 indexed
state rows, 16 MiB encoded state, 32 MiB audit bodies, 32 KiB per row, 128 MiB
database, 32 MiB WAL, and 1 MiB shared-memory sidecar. Budgets may be lowered,
not raised beyond these ceilings. This is a local operator storage profile,
not an enterprise throughput benchmark or a quota over canonical CAS/artifacts.

SQL size/count checks precede Python projection materialization and JSON
decoding; database/sidecar confinement and size checks precede SQLite opening.
The entire admitted audit chain is still hash-verified. There is no truncation,
history pruning, hash cache, silent migration or fabricated verification result.
An existing over-budget store fails closed and needs an explicit governed
storage decision. Capacity errors expose stable codes, not paths or internals.
At the exact admitted event ceiling, read-only source/status/timeline/audit
operations stay readable. Further mutations, including no-op write requests,
may return 429; they must not be displayed as successful operations.

Before dispatch, an actual operator worker reserves three catalogue receipt
credits (start, native outcome, finish) plus conservative audit-byte headroom.
Reservations are durable hash-bound catalogue state. Other producers cannot
spend them. Normal completion or a paused/cancelled no-dispatch finish consumes
the needed receipts and releases unused credits. A process crash does not
automatically reclaim them: stale worker evidence requires governed review.
This reserves catalogue receipts only; it does not make canonical queue,
persistence, CAS and catalogue writes a distributed transaction. Crash/control
reconciliation, parser-process isolation, aggregate CAS/storage quotas, producer
trust, supported-POSIX QA003, and the full-section re-audit remain open.

## Current mutable H1-003 candidate (not yet a final section seal)

[H1-003 specification](../../docs/section18/H1_003_SPEC.md) supersedes the
historical parser/cancellation observations above **only** for these tested
scopes: source parsing is delegated to a genuinely OS-bounded child; controlled
worker CLI execution has independent parent wall-time/output supervision; queued
cancellation has durable intent, partial-transition replay and exact completion
proof. Canonical engine/infrastructure code remains unchanged.

The current dedicated local suite passes 31 distinct methods. A previous 590-
method cumulative pass predates the final concurrency/worker-supervision changes
and is retained as historical evidence, not a current full-suite receipt.
Supported-Linux current-candidate validation, aggregate CAS/storage quotas,
crashed-worker receipt recovery, full33 capability/security re-audit, final master
fresh extraction and integration gates are still open. Task028 remains paused.
