# BIE-QA-HARD-015 — Native math-parser completeness contract

## Original audit scope
Repair or isolate the pinned native expression-parser mismatch through owner-reviewed compatibility work; audit latest canonical version before changing it.

## Original closure obligations (preserved)
- Original x * y + z parses without dropping the addition.
- Full expression consumption, precedence and round-trip/negative tests pass.
- Strict adapter remains protective; no unreviewed overwrite of canonical code.

## Implemented local behavior
Reinspects current canonical parser, preserves it, and isolates its partial-consumption behavior using an additive full-consumption Pratt parser returning native Node values. Checks precedence, associativity, unary signs, round trips, token/node/depth limits and the inherited independent strict-expression parser.

## Remaining operational scope
- The native parser itself remains unchanged and unsafe for unsupported calls that bypass the complete adapter.
- Owner-reviewed canonical caller migration, whole-repository compatibility checks and post-merge verification remain open.

## Source and evidence
- `bie/qa/domain_quality_v2/common.py`
- `bie/qa/domain_quality_v2/parser.py`

Shared test suite: `tests/qa_hardening_h4` (211 unique methods across all six tasks; do not multiply). Executed receipt: `hardening/section16_h4/evidence/final_source_suites/TEST_RESULT.json`. Mutation and diagnostic receipts are adjacent under `evidence/`. Specifications do not substitute for those executions.

## Integration boundary
Native APIs and original source artifacts remain unchanged. This is additive local code with full local regression, not canonical repository integration. No production PASS/certificate, source semantic clearance or learner mastery is issued. All 113 historical/audit obligations remain authoritative; none is closed by this task.
