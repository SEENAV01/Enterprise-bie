# BIE-QA-HARD-016 — Cinematic narrative and multilingual script rubric

## Original audit scope
Evaluate explanatory hook/payoff, source fidelity, pacing and purposeful cinematic direction on actual native scripts and renders, not slide decoration.

## Original closure obligations (preserved)
- Engaging-but-wrong and technically-valid-but-unexplained examples fail the relevant floor.
- Condition omission, repetition, Hindi/English terminology and narration timing have tests.
- Scientific content stays correct when simplified; objective coverage remains mandatory.

## Implemented local behavior
Executes native ScriptPlan validation and binds source conditions, objective/segment inventories, explanatory hook/payoff, literal Hindi/English terminology, text-based timing and independent per-criterion floors. Supplied ratings cannot establish semantic approval; every healthy result still requires review.

## Remaining operational scope
- Operational independently calibrated rubric assessment and native rendered cinematic/teaching quality remain open.
- Measured bilingual speech, timing and perception, semantic repetition detection, and real learner outcomes remain open.

## Source and evidence
- `bie/qa/domain_quality_v2/common.py`
- `bie/qa/domain_quality_v2/director.py`

Shared test suite: `tests/qa_hardening_h4` (211 unique methods across all six tasks; do not multiply). Executed receipt: `hardening/section16_h4/evidence/final_source_suites/TEST_RESULT.json`. Mutation and diagnostic receipts are adjacent under `evidence/`. Specifications do not substitute for those executions.

## Integration boundary
Native APIs and original source artifacts remain unchanged. This is additive local code with full local regression, not canonical repository integration. No production PASS/certificate, source semantic clearance or learner mastery is issued. All 113 historical/audit obligations remain authoritative; none is closed by this task.
