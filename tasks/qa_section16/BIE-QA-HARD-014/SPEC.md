# BIE-QA-HARD-014 — Broader mathematics, units and precision adapters

## Original audit scope
Add governed capability coverage for required textbook math beyond rational-polynomial scalar/real-SI profiles, using registered tools and conditions.

## Original closure obligations (preserved)
- Representative calculus/vector/matrix and extended-unit fixtures are independently checked.
- Extraneous/lost solutions and numerical precision/unit errors are detected.
- Unsupported mathematics never receives a universal-solver claim.

## Implemented local behavior
Adds exact polynomial differentiation/antiderivative checking and definite integration; rational matrices, unique linear systems with pivoting, dot/cross products, explicit extended-unit scales and complete rational real root sets for linear/quadratic cases. Tolerances are operator-controlled and exact by default.

## Remaining operational scope
- General symbolic/nonpolynomial calculus, complex solutions, tensors, broader units and mathematical OCR remain unsupported or review-required.
- Independent reference/source interpretation and canonical mathematics-to-render integration remain open; finite exact equality is not empirical-law truth.

## Source and evidence
- `bie/qa/domain_quality_v2/common.py`
- `bie/qa/domain_quality_v2/mathematics.py`

Shared test suite: `tests/qa_hardening_h4` (211 unique methods across all six tasks; do not multiply). Executed receipt: `hardening/section16_h4/evidence/final_source_suites/TEST_RESULT.json`. Mutation and diagnostic receipts are adjacent under `evidence/`. Specifications do not substitute for those executions.

## Integration boundary
Native APIs and original source artifacts remain unchanged. This is additive local code with full local regression, not canonical repository integration. No production PASS/certificate, source semantic clearance or learner mastery is issued. All 113 historical/audit obligations remain authoritative; none is closed by this task.
