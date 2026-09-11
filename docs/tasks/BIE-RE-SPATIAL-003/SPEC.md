# BIE-RE-SPATIAL-003 — Map reasoning

Status: IMPLEMENTED, NOT ACCEPTED.

Dependencies: BIE-RE-SPATIAL-001, BIE-RE-SPATIAL-002. All checked against actual implementations and passing regression evidence.

Implementation: `bie/reasoning/map_reasoning.py`. Contract and scope: `docs/REASONING_BATCH_SPATIAL_TEMPORAL.md`.

Task tests: 16 passing in `tests/reasoning/test_map_reasoning.py`. Shared result lineage uses existing BIE evidence/decision/artifact contracts. Integrated regression evidence: `validation/integrated_tests.json`.

Real-book integration and downstream executable production evidence remain required for acceptance.

## Quality review 001

Implementation revision 1. The original 16 task tests remain passing, plus 1 additional checks in `tests/reasoning/test_section_quality_review.py`. See `docs/evidence/reasoning-quality-001/REVIEW.md` for reproduced defects, independent oracles and remaining acceptance gates.
