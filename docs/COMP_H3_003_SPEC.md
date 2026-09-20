# BIE-COMP-H3-003 — Reduced-motion producer/consumer

Parent checkpoint: BIE-COMP-H2-005. Audit basis: H2-R02_WHOLE_SCENE_CONSUMERS_ACCESSIBILITY.

## Bounded requirement
Resolve explicitly referenced source-bound reduced-motion variants into opacity tracks or fixed analytic-model samples; retain original/effective identity and provenance. Refuse unknown variants and dynamic families without adapters.

## Execution
`PYTHONPATH=app:. python -m unittest tests.compiler.test_comp_h3_003 -v`

See COMP_H3_SPEC.md for contract fields and COMP_H3_REAUDIT.md for evidence limits and remaining gaps. Source/test/bridge success is not real rendering or product acceptance.

## Evidence
Real task log: validation/comp_h3/atomic_tests/H3_003_TEST_RESULT.txt. Full regression: validation/comp_h3/REGRESSION_FINAL.txt. Fresh atomic ZIP extraction logs are included in the outer master backup verification evidence.

Status: IMPLEMENTED_BOUNDED_LOCAL_TESTED, PRODUCT_NOT_ACCEPTED. No GitHub modification.
