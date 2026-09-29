# BIE-QA-HARD-037 — Operational rights inventory and output notices

## Original scope
Bind real source/asset/provider/dependency inventories, scoped permission evidence and actual published notices.

## Dependencies
BIE-QA-HARD-006, BIE-QA-HARD-007, BIE-QA-HARD-020, BIE-QA-HARD-022, BIE-QA-HARD-035

## Implemented local contract
Reuses the inherited rights evaluator over exact source/asset/dependency/provider inventory and independently signed clearance. Required notice channels are bound to exact output/capture bytes and observation types. The full trusted-time interval must fit permission validity.

## Original closure criteria (preserved)
- Unknown ownership/status or missing upstream permissions remains blocked/review-required.
- Rendered credits and source offers match approved terms.
- Qualified clearance is externally evidenced; synthetic permissions are never promoted.

## Remaining closure requirements
- No real ownership or legal clearance, live grant-status service, qualified external rights reviewer or native rendered/deployed notice validation was executed. Submitted capture assertions remain dependent on independently trustworthy capture evidence.
- The saved Money.pdf is an analysis source, not a cleared distribution asset; its full bytes are deliberately excluded from this delivery.

## Evidence
Code: bie/qa/assurance_quality_v2/rights.py
Shared suite: tests/qa_hardening_h8 (155 unique methods; do not multiply per task).
Executed receipt: hardening/section16_h8/evidence/final_source_suites/TEST_RESULT.json
Mutations: hardening/section16_h8/evidence/mutations/MUTATION_RESULT.json
Diagnostics: hardening/section16_h8/evidence/diagnostics/EXECUTION_RESULT.json

## Authority and acceptance
Inputs, identities and authority are operator configuration, not permissions granted by a source document. Failures and missing native/rights/assessment evidence block or require review. No inherited policy or acceptance floor is relaxed. No GitHub, Section15, global continuation, credential service or live memory mutation. Local implementation is not operational closure.
