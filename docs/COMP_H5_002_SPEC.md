# BIE-COMP-H5-002

2D orthographic camera focus/zoom consumer with frame-indexed projection and exhaustive layer-envelope parity

Governed source: existing H3-R02 in the consolidated ledger. No new full section audit.

See `docs/COMP_H5_SPEC.md` for exact contracts, producer/consumer boundaries, failure behavior and evidence limits.

Atomic suite: `PYTHONPATH=app:. python -m unittest tests.compiler.test_comp_h5_002 -v` (19 test methods).

Delivery is an ORDERED DELTA: exact H4 baseline plus all preceding H5 deltas required. Do not overlay onto unrelated or modified source. Full integrated workspace is separately provided.

Implementation/test status is not product acceptance.
