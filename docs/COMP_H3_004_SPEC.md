# BIE-COMP-H3-004 — Isolated mathematical worker and host identity

Parent checkpoint: BIE-COMP-H2-005. Audit basis: H2-R03_TOOLCHAIN_IDENTITY_EXECUTION_SAFETY.

## Bounded requirement
Perform production math typesetting in a bounded sanitized child; bind host Python/backend/native/font and compiler byte identities into cache keys; verify child identity and resource receipt. Not an OS security sandbox.

## Execution
`PYTHONPATH=app:. python -m unittest tests.compiler.test_comp_h3_004 -v`

See COMP_H3_SPEC.md for contract fields and COMP_H3_REAUDIT.md for evidence limits and remaining gaps. Source/test/bridge success is not real rendering or product acceptance.

## Evidence
Real task log: validation/comp_h3/atomic_tests/H3_004_TEST_RESULT.txt. Full regression: validation/comp_h3/REGRESSION_FINAL.txt. Fresh atomic ZIP extraction logs are included in the outer master backup verification evidence.

Status: IMPLEMENTED_BOUNDED_LOCAL_TESTED, PRODUCT_NOT_ACCEPTED. No GitHub modification.
