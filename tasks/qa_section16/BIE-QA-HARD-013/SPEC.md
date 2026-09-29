# BIE-QA-HARD-013 — Native pedagogy routes and assessment integration

## Original audit scope
Connect actual lesson branches, objectives, misconception remediation and assessments to QA; distinguish planned opportunity from measured learning.

## Original closure obligations (preserved)
- Bad nondefault routes, answer leakage and deficient transfer exercises fail.
- Route inventory is authoritative and matches observed behavior.
- Audience/language load guardrails remain explicit until empirical calibration.

## Implemented local behavior
Executes native LessonArchitecture validation and AssessmentBlueprint coverage. Checks independently enumerated routes, transfer demand, response windows, answer leakage, remediation and trace freshness. Submitted observed labels do not prove learner mastery or runtime authenticity.

## Remaining operational scope
- Genuine runtime traces, native lesson/player integration and authenticated observations remain open.
- Actual learner outcomes, comprehensive remediation/transfer validity and empirical audience/language load calibration remain open.

## Source and evidence
- `bie/qa/domain_quality_v2/common.py`
- `bie/qa/domain_quality_v2/pedagogy.py`

Shared test suite: `tests/qa_hardening_h4` (211 unique methods across all six tasks; do not multiply). Executed receipt: `hardening/section16_h4/evidence/final_source_suites/TEST_RESULT.json`. Mutation and diagnostic receipts are adjacent under `evidence/`. Specifications do not substitute for those executions.

## Integration boundary
Native APIs and original source artifacts remain unchanged. This is additive local code with full local regression, not canonical repository integration. No production PASS/certificate, source semantic clearance or learner mastery is issued. All 113 historical/audit obligations remain authoritative; none is closed by this task.
