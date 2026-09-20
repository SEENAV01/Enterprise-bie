# BIE-COMP-H3-002 — Content-fit evidence validation

Parent checkpoint: BIE-COMP-H2-005. Audit basis: H2-R01_FRAME_AWARE_LAYOUT.

## Bounded requirement
Consume exhaustive source-bound browser measurements; detect text/legend overflow and below-policy text/equation scale; reject missing frames, forged scope and stale evidence. No automatic shrinking or whole-product acceptance.

## Execution
`PYTHONPATH=app:. python -m unittest tests.compiler.test_comp_h3_002 -v`

See COMP_H3_SPEC.md for contract fields and COMP_H3_REAUDIT.md for evidence limits and remaining gaps. Source/test/bridge success is not real rendering or product acceptance.

## Evidence
Real task log: validation/comp_h3/atomic_tests/H3_002_TEST_RESULT.txt. Full regression: validation/comp_h3/REGRESSION_FINAL.txt. Fresh atomic ZIP extraction logs are included in the outer master backup verification evidence.

Status: IMPLEMENTED_BOUNDED_LOCAL_TESTED, PRODUCT_NOT_ACCEPTED. No GitHub modification.
