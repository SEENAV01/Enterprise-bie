# BIE-COMP-H3-001 — All-frame spatial envelopes

Parent checkpoint: BIE-COMP-H2-005. Audit basis: H2-R01_FRAME_AWARE_LAYOUT.

## Bounded requirement
Evaluate every rendered frame of supported nested 2D tracks, viewport bounds and conservative layer-box overlap; preserve intentional overlap declarations; refuse uncovered/budget-exceeded work. No ink or continuous-time claim.

## Execution
`PYTHONPATH=app:. python -m unittest tests.compiler.test_comp_h3_001 -v`

See COMP_H3_SPEC.md for contract fields and COMP_H3_REAUDIT.md for evidence limits and remaining gaps. Source/test/bridge success is not real rendering or product acceptance.

## Evidence
Real task log: validation/comp_h3/atomic_tests/H3_001_TEST_RESULT.txt. Full regression: validation/comp_h3/REGRESSION_FINAL.txt. Fresh atomic ZIP extraction logs are included in the outer master backup verification evidence.

Status: IMPLEMENTED_BOUNDED_LOCAL_TESTED, PRODUCT_NOT_ACCEPTED. No GitHub modification.
