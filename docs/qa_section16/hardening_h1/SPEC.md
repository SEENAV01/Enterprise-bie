# H1 — Release boundary hardening specification

## Scope and provenance
This is a continuation of Section16 Audit001, not a restart, Section17, canonical
GitHub integration, or a production release. The original 76 tasks remain intact.
Implements the registered HARD001..004 local contracts. The historical registry and
all inherited obligations remain preserved. Section15 belongs to the other work session.

## HARD001: typed terminal reports and blocker propagation
`publication_v2.terminal` registers `bie.qa.terminal-report/1` and an explicit typed
obligation ledger. Unknown schemas, versions, fields, enums, malformed arrays and
unregistered policies fail closed; there is no status-only fallback or filename-based
bypass. Each check has an ID, status, typed diagnostics and child checks. Every child
is traversed with depth/count bounds. Mandatory check identities are set out of band
in `PublicationPolicy.terminal_requirements`, never accepted from the request.
Duplicate check/diagnostic/obligation IDs are rejected. Failed, skipped, unknown,
review-required and pending statuses cannot be averaged away by an outer PASS.

The exact inherited Section16 `1.0.0` ledger grammar recognizes `gaps`, four
batch-specific obligation arrays and `audit001_findings`. It retains all113 submitted
rows (101 inherited obligations plus12 audit findings). Unknown collections fail
closed. A legacy ledger can veto; it cannot authorize because it has no subject/time
bindings. A typed ledger may support a typed report and requires actual closure-file
bytes for a CLOSED row. Authoritative completeness and independent correctness of
closure evidence remain HARD006. A removed/omitted upstream inventory is not claimed
solved by this batch. No old ledger row is silently closed.

## HARD002: transitive binding and evidence lifetime
Terminals bind their own report ID, subject type/ID, evidence ID, candidate digest,
run, revision, release policy digest, independently configured evaluator-policy digest,
complete inspected ArtifactRefs and (for section exit) the final bundle digest. Gate
reports omit the circular final-bundle binding explicitly with null, not an arbitrary
missing field. All inspected/auxiliary bytes are re-read through SnapshotStore with
alias, path and hash checks; the graph records these dependencies.

Captured, created and expiry clocks are integers with bounded lifetimes. Future,
expired, stale-capture or impossible-order reports block. An outer receipt cannot
create a valid inner report or conceal its expiry. Certificate expiry is capped by
each terminal and key validity bound. Rereading at issue/verify remains mandatory.

The separate `bie.qa.immutable-fact/1` admits only exact artifact identity plus a
nonempty justification. It has no verdict or time claim and cannot satisfy a gate.
It may only support an already time-bound typed terminal. No generic timeless
execution, rights, calibration or section-completion exemption exists.

## HARD003: monotonic diagnostics and legacy behavior
All v2 `GateEvidence.diagnostics` strings are blocking, regardless of text or outer
status. Prefixing a string with ADVISORY cannot downgrade it. Typed terminal
Diagnostic records distinguish BLOCKING from ADVISORY; advisory notes remain in the
evidence graph and never excuse a failed check. Both release_v2 and publication_v2
retain blocker codes. Optional/not-applicable legacy modes cannot discard a supplied
blocking diagnostic. Unknown legacy gates are reported and block.

The active metadata-only `bie.qa.release_contracts` no longer returns SUCCESS; a
healthy metadata assessment returns CONTRACT_ONLY, or READY_FOR_REVIEW under its
human-review option. Its decision explicitly carries release_authorized=false,
product_accepted=false, and LEGACY_METADATA_ONLY scope. The legacy v2 preview remains
BLOCKED. Original source is retained under history, NOT as a supported production API.
Never import historical snapshots into a production caller.

## HARD004: independent evaluators and local key lifecycle
TrustedKey is provisioned out of band with principal_id and independence_group.
Readiness requires independent principal, group and credential counts as well as
existing evaluator-name/report-byte floors. Shared secrets may not identify conflicting
principals/groups; rotated keys for the same principal do not create another reviewer.
Unmapped old keys conservatively share one legacy-unclassified group and cannot satisfy
an independence floor of two. Their signatures remain usable for a floor-one contract.

not_before/not_after/enabled/revoked_at govern local validity. GateEvidence cannot
claim pre-key creation or exceed key lifetime. The assessment clock is passed explicitly
through verify_at; clockless verifier plugins do not authorize readiness. The legacy
verify method is signature inspection at an explicitly supplied or record-creation
clock, not current readiness. Publication caps expiry and rechecks revocation at issuance
and verification. Keys are immutable snapshots: operational refresh/revocation
propagation remains HARD035. HMAC is not remote attestation or asymmetric signatures.

## Compatibility and migration
No old source or test is discarded. Current code is intentionally corrected in place;
adding an unused wrapper would leave the vulnerable readiness paths usable.
Originals are preserved in history/section16_pre_h1 with exact hashes. Four inherited
test files have documented compatibility migrations: typed synthetic report fixtures,
stricter unsupported-schema diagnostics, metadata-only CONTRACT_ONLY expectations,
and preimage hash assertions. Their counts and all negative checks are retained.
The complete inherited 3529 suite-qualified cases are executed on the corrected code.
The same3529 passed separately on the unmodified baseline before edits.

Native consumers must produce registered typed reports with a reviewed adapter and
out-of-band evaluator-policy requirements. Wrapping a generic PASS is not a migration.
Historical evidence is retained but cannot automatically authorize the new policy.
No candidate JSON can register schemas, callbacks, keys or authority configuration.

## Validation and boundaries
Run `python -B scripts/verify_qa_section16_h1.py --output /new/path --workers 4`.
Run `python -B scripts/mutate_qa_section16_h1.py --output /another/new/path`.
All outputs must be new paths outside a frozen release package. The tests use synthetic
subjects, times and authority. Positive certificates are DIAGNOSTIC_ONLY. No native
book-to-video/game, current GitHub regression, operational assessor, KMS or production
publication is executed. This is a local contract closure, not section exit or product
acceptance. HARD005/006 are the next registered tasks; all37 later tasks remain open.
