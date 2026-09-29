# Section16 H2 specification — HARD005 / HARD006

## Scope and authority
HARD005 normalizes local task, source, specification, suite, evidence and integration
metadata. HARD006 binds terminal publication to an independently configured required
artifact/check/task/obligation census. This is not canonical repository integration.

## Task/integration index
The frozen baseline preserves76 original tasks,22 original QA namespaces,41 audit
hardening tasks,101 inherited obligations and12 audit findings. The new governance_v2
namespace is additional (23 total). The original task terminology, source namespace
and historical evidence paths remain traceable. Current function/class source spans
and file hashes are recomputed; historical success records do not establish current
acceptance. Every case identity includes suite, source path and method identifier.

Index generation requires all registered suites, exact test counts, current source
and test hashes, every original task, every hardening task and every namespace.
Continuation, current task result and normalized integration plan must agree.
Metadata cannot claim integration or product acceptance. Verification regenerates
the complete map from an independently pinned blueprint, not from the submitted index.
The read-only CLI accepts a blueprint digest supplied independently by the operator.
The local filesystem reader rejects traversal, links, missing/nonregular files and
bounded-size violations; it is not a hostile concurrent-filesystem sandbox.

## Required inventories
InventoryAuthority is a Python object installed out-of-band in PublicationPolicy.
PublicationRequest adds only a reference to an inventory declaration; JSON cannot
supply a trust store or replace the policy. Missing authority or inventory blocks
the active publication assessor and hence certificate issuance. Existing request
JSON without the new field remains parseable but cannot obtain readiness.

The authority fixes artifact identity/path/size/hash/role, required original and
hardening task IDs, per-gate and section-exit check IDs, and obligation definitions.
Declaration membership is compared exactly; omitting a row cannot shrink a floor.
Production requires the SECTION16 profile, which contains all117 baseline task IDs
and113 obligation/finding IDs and exact frozen definition digests. DIAGNOSTIC can
use smaller test inventories but cannot authorize production. Additional approved
requirements may be added; known baseline requirements cannot be removed.

## Closure evidence
OPEN, EXTERNAL_PENDING, PARTIALLY_ADDRESSED_OPEN, PENDING and BLOCKED remain blocking.
A CLOSED string requires actual closure-file bytes and typed terminal evidence,
current candidate/run/revision, exact obligation/owner/scope/definition/configuration,
required checks and affected artifacts. Every dependency is read and hash-checked.
Missing, failed, skipped, uncertain, unregistered or altered evidence blocks.

Purpose-scoped closure signatures use separately configured HMAC principals/groups/
credentials. All fields except the approval list are signed with domain separation.
Duplicate approvals, aliases, inadequate independent quorum, wrong purposes, revoked
or expired keys, future/expired closures and test-only production credentials block.
Inventory/closure/report/key lifetimes cap certificate lifetime. Any authority or
candidate revision change invalidates all old closures conservatively; selective
closure migration is not implemented. Key fingerprints, never secrets, enter public
policy serialization. HMAC configuration is not a deployed KMS or remote attestation.

## Preservation and compatibility
Active publication contracts, codec, evaluator and terminal subject policy are
updated. One inherited fixture is migrated to explicit synthetic authority and its
request schema gains a nullable inventory ref. No inherited test is deleted/skipped.
Preimages remain under history/section16_pre_h2. The original gap ledger and audit
registry remain byte-identical. The normalized integration plan keeps historical
verify-only dependency references explicitly historical, not as current-HEAD facts.

## Testing and boundaries
133 unique H2 tests and3647 inherited tests ran successfully.16 targeted safeguard
removals were detected with passing controls.11 authored diagnostic evaluations
include two positive controls, missing inventories, invalid closure and the real
113-entry catalogue. Positive media and credentials are synthetic; zero historical
obligations or production certificates are closed/issued here. Structural JSON
schemas are supplied for inventory, closure and index; runtime checks are stricter.

Operators must still independently establish that required output/check inventories
are complete for a real run. This implementation does not automatically discover
arbitrary unlisted source concepts, execute native engines, validate reviewer
judgment, provision live authorities or complete real-book acceptance. Subsequent
native adapters and operational hardening remain mandatory. Section15 is external.

## Reproduction
See README_QA_SECTION16.md for the pinned-index command.
`python -B scripts/verify_qa_section16_h2.py --output /tmp/new-h2-run --workers 4`
runs the complete local corpus in isolated suites.
`python -B scripts/diagnose_qa_section16_h2.py /tmp/new-h2-diagnostics`
executes the11 synthetic-authority file diagnostics. Output paths must be new.
Keep execution output outside the immutable package.
