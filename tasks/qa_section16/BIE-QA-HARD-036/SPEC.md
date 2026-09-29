# BIE-QA-HARD-036 — Canonical regression corpus and test identity

Owner: QA.INFRA. Local namespace: `bie/qa/lifecycle_quality_v2`.

## Original scope (preserved)
Register full canonical cases, immutable expected outputs and suite-qualified identities; run all native consumers, not only the local subset.

## Required full-closure evidence (preserved)
- Missing cases, altered fixtures and duplicate record identities fail.
- Before/after semantic, pixel and game-state regressions include negative controls.
- The 3529 local cases are not relabelled as full-repository coverage.

## Local implementation
Checks a supplied Git checkout against independently pinned revision/tree and every raw tracked blob, rejects dirty/untracked/omitted test files, discovers suite-qualified cases, and executes the independently approved immutable registration in isolated processes.

## Inputs, outputs and trust
All mutable target paths, required validators, policies, source/fixture inventories and authority are operator inputs. Candidate/document text cannot grant privileges, weaken gates or authorize its own changes. Reports/receipts identify exact artifact bytes, run, revision, candidate and policy. Proposed fixes do not modify the original and cannot inherit old signatures.

## Executed test/evidence locations
- `tests/qa_hardening_h6/test_corpus.py`
- `hardening/section16_h6/evidence/final_source_suites/TEST_RESULT.json`
- `hardening/section16_h6/evidence/mutations/MUTATION_RESULT.json`
- `hardening/section16_h6/evidence/diagnostics/EXECUTION_RESULT.json`

The 137-case H6 suite is shared, not an independent count per task. Positive review credentials and human/model observations are explicitly synthetic.

## Remaining requirements
- Only two authored two-test Git repositories exercised full discovery/execution; the full Enterprise-bie checkout is not mounted and was explicitly rejected rather than substituted.
- The cumulative local suite count is not canonical regression coverage. Broader frameworks, third-party dependency closure, production worker isolation and latest canonical corpus execution remain open.

No historical obligation is closed here. Section15, GitHub and global continuation are unchanged. Final section audit and canonical real-book gates remain required.
