# BIE-QA-HARD-012 — Domain reasoning and condition-preservation checks

## Original audit scope
Extend beyond bounded propositional inference through registered causal, spatial and temporal validators or explicit review adapters.

## Original closure obligations (preserved)
- Causal versus correlational reasoning, chronology and coordinate-frame counterexamples are rejected.
- Unsupported logic is review-required, not formal proof.
- Actual native reasoning evidence is consumed without overwriting the reasoning engine.

## Implemented local behavior
Consumes native ReasoningDecision/ReasoningDecisionGraph, exact source text and operator-bound causal, chronology and affine-coordinate models. Checks dropped conditions, correlation promoted to causation, reversed/uncertain chronology and common-frame counterexamples. Unknown reasoning remains review-required.

## Remaining operational scope
- Independent validity of causal/chronology/frame models and natural-language interpretation remains open.
- Broader causal/counterfactual/temporal/spatial profiles and native downstream lesson/render integration remain open.

## Source and evidence
- `bie/qa/domain_quality_v2/common.py`
- `bie/qa/domain_quality_v2/reasoning.py`

Shared test suite: `tests/qa_hardening_h4` (211 unique methods across all six tasks; do not multiply). Executed receipt: `hardening/section16_h4/evidence/final_source_suites/TEST_RESULT.json`. Mutation and diagnostic receipts are adjacent under `evidence/`. Specifications do not substitute for those executions.

## Integration boundary
Native APIs and original source artifacts remain unchanged. This is additive local code with full local regression, not canonical repository integration. No production PASS/certificate, source semantic clearance or learner mastery is issued. All 113 historical/audit obligations remain authoritative; none is closed by this task.
