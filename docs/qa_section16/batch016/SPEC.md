# Section16 Batch016 — repair evidence and repair regression

## Scope and inputs
Original registry page18: BIE-QA-REPAIR-012 repair evidence and BIE-QA-REPAIR-013
repair regression. This is additive `bie/qa/repair_audit_v2`, not a replacement for
repair_v2, domain_repair_v2, media_repair_v2 or the canonical orchestrator.
The original snapshot, policies, generated replacement files, failure reports,
proposal, completed attempt, journal export and detailed before/after observations
are separate byte-hashed artifacts. The operator supplies executable validators
and required cases independently of candidate data. No JSON import or shell command
field is interpreted as executable code.

## REPAIR-012 evidence inspection
Recompute proposal/base/policy and attempt receipt identities; independently derive
the after-snapshot from approved replacement bytes; verify the complete staged file
inventory and unchanged originals. Recompute the SQLite export event chain and
reservation-to-finish correspondence, attempt numbering, proposal/effect identity,
byte/time limits, freshness and all downstream invalidations. Missing, unfinished,
replayed, renumbered or post-staging journal entries cannot authorize the attempt.
Historical staged_directory is never followed as filesystem authority.
A hash chain alone is not a signature or proof of execution. Original failure
inventory and proposal approvals must be valid at reservation time. A separate
current execution assessment covers the complete audit request and its exact
artifact identities. Missing or rejected authorization never produces CHECKS_PASSED.
Optional required generation links verify actual job, policy, limits, witness and
replacement bytes from the inherited deterministic domain/media generator format.
The source-generation path was executed in this batch; this is not a claim of new
native video, game or live-model execution.

## REPAIR-013 regression inspection
AuditPolicy maps every targeted failure to a specific required baseline case. The
required check dependency closure cannot be reduced by the repair. Baseline and
candidate run independently on disposable private copies using source-pinned,
operator-registered validators. Protected fixture bytes are identical. Each case
returns explicit PASS/FAIL/REVIEW/NOT_RUN/ERROR and a nonempty canonical witness.
A repair target must reproduce a real FAIL before and PASS after. Previously passing
cases may not regress; every required candidate case must pass. Missing/renamed/
duplicate cases, changed validators, changed fixtures, reused execution IDs and
unexecuted/stale/failed worker evidence block the audit. Aggregate pass percentages
never override an individual failing required case.

## Execution and interfaces
`collect_regression(snapshot, proposal, original_root, candidate_root,
repair_policy, audit_policy, registry=..., as_of=...)` executes before/after workers.
`evaluate(request, original_root, candidate_root, repair_policy, audit_policy,
as_of=..., inventory_reviews=..., proposal_reviews=..., audit_reviews=...,
verifier=...)` reads and verifies the evidence; it does not manufacture reviews.
Only `collect_regression` executes validators. Standalone audit is read-only.
Three structural JSON schemas accompany strict runtime dataclass decoding. Neither
schema validation nor CHECKS_PASSED grants release or full-repository acceptance.

### Unsigned CLI
```
python -B -m bie.qa.repair_audit_v2 request.json repair-policy.json audit-policy.json \
  --original-root ORIGINAL --candidate-root STAGED --as-of UNIX_SECONDS \
  --output NEW_REPORT.json
```
CLI does not accept signing secrets or load callbacks from the request. Exit2 is
blocked,3 requires review,4 is invalid input/output. Existing output is never
silently overwritten. Output must be outside source/staged roots. Caller-provisioned
API reviews are required for a fully authenticated bounded check.

## Security and evidence boundaries
Workers have POSIX resource/time bounds and are terminated by process group. They
are trusted local callbacks, NOT a hostile-code sandbox. Source/module hashes do
not pin every transitive import. Complete caller environment, distributed journal,
protected remote attestation and canonical integration remain open.
The as_of policy clock is explicitly provided; actual worker wall-clock nanoseconds
and environment identity are also recorded. Local case completeness depends on the
operator's registry and is not comprehensive scientific/semantic validation.
All positive demo/test approvals are SYNTHETIC. Native media/game/browser, live
assessor reliability, learner outcomes and real-book end-to-end proof remain open.
The release bridge re-audits inputs and emits unsigned FAIL or NOT_RUN for the full
regression gate; never PASS. The inherited complete release evaluator remains blocked.

## Reproduce
```
python -B scripts/verify_qa_repair_audit16_batch016.py --output NEW_EVIDENCE_DIR
python -B scripts/verify_qa_repair_audit16_mutations.py --output NEW_MUTATION_DIR
python -B scripts/demo_qa_repair_audit16.py --output NEW_DIAGNOSTIC_DIR
python -B scripts/recheck_qa_repair_audit16_diagnostics.py \
  evidence/qa_section16/executed_run_016/diagnostics
python -B scripts/verify_qa_section16_package.py
```
Python dependencies are inherited from the cumulative package. New audits use the
standard library and existing BIE modules; schema tests also use jsonschema. Actual
subprocess execution requires POSIX/fork; unsupported platforms fail explicitly.
