# BIE-QA-HARD-029 — Durable orchestration and crash recovery

Owner: INFRA.QA.REPAIR. Local namespace: `bie/qa/lifecycle_quality_v2`.

## Original scope (preserved)
Bind local journals to canonical task invalidation/idempotency and durable transactional state.

## Required full-closure evidence (preserved)
- Crash/resume, duplicate delivery and competing reservations cannot double-publish or reset budgets.
- Cancellation/timeouts terminate whole registered process groups and preserve evidence.
- Distributed recovery is explicitly tested when that deployment is enabled.

## Local implementation
Transactional local SQLite lease/fencing/attempt budgets, hash-chained state projection and result/invalidation outbox; committed-claim crash recovery and competing processes exercised. Native invalidation contract executes on exact causal descendant sets.

## Inputs, outputs and trust
All mutable target paths, required validators, policies, source/fixture inventories and authority are operator inputs. Candidate/document text cannot grant privileges, weaken gates or authorize its own changes. Reports/receipts identify exact artifact bytes, run, revision, candidate and policy. Proposed fixes do not modify the original and cannot inherit old signatures.

## Executed test/evidence locations
- `tests/qa_hardening_h6/test_durable_workers.py`
- `tests/qa_hardening_h6/test_schemas_cli.py`
- `hardening/section16_h6/evidence/final_source_suites/TEST_RESULT.json`
- `hardening/section16_h6/evidence/mutations/MUTATION_RESULT.json`
- `hardening/section16_h6/evidence/diagnostics/EXECUTION_RESULT.json`

The 137-case H6 suite is shared, not an independent count per task. Positive review credentials and human/model observations are explicitly synthetic.

## Remaining requirements
- Local trusted-directory durability, not distributed deployment, trusted wall-clock service, adversarial DB administration/rollback defense or exactly-once remote publication.
- Lease expiry does not terminate the old worker. Fencing prevents stale commits; worker process-group cancellation is separate and only trusted callbacks are supported. Canonical orchestrator dispatch remains open.

No historical obligation is closed here. Section15, GitHub and global continuation are unchanged. Final section audit and canonical real-book gates remain required.
