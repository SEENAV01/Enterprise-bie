# BIE-COMP-H3-005 — Hardened source and render-path adoption

Parent checkpoint: BIE-COMP-H2-005. Audit basis: H2-R01/H2-R02/H2-R03.

## Bounded requirement
Adopt H3 in the default publication CLI and mandatory real-render source gate; recompute identity/variant/layout/source checks at use; retain legacy source-only diagnostic APIs, history and exact evidence distinctions.

## Execution
`PYTHONPATH=app:. python -m unittest tests.compiler.test_comp_h3_005 -v`

See COMP_H3_SPEC.md for contract fields and COMP_H3_REAUDIT.md for evidence limits and remaining gaps. Source/test/bridge success is not real rendering or product acceptance.

## Evidence
Real task log: validation/comp_h3/atomic_tests/H3_005_TEST_RESULT.txt. Full regression: validation/comp_h3/REGRESSION_FINAL.txt. Fresh atomic ZIP extraction logs are included in the outer master backup verification evidence.

Status: IMPLEMENTED_BOUNDED_LOCAL_TESTED, PRODUCT_NOT_ACCEPTED. No GitHub modification.
