# BIE-COMP-H7-003 — Installed toolchain identity

Parent: BIE-COMP-H6-005. Finding: R03.

## Required behavior
Manifest every installed dependency file and internal symlink; exact lockfile/version binding; Node/browser/native assets and immutable replay checks.

## Execution and boundaries
This task's implementation is part of the cumulative H7 integration. Restore all eight ordered deltas before executing task suites; intermediate delta trees are assembly states, not standalone runnable applications.

```bash
PYTHONPATH=app:. python -m unittest tests.compiler.test_comp_h7_003 -v
```

Targeted suite: 15 tests. Full release/package evidence is externally bound to the final integrated ZIP. Real Remotion and browser sandbox execution remain blocked; the local browser bridge has explicit API doubles and cannot authorize a production render. See `docs/COMP_H7_REAUDIT.md` for exact unclosed broader findings. Product accepted: false.

## Failure and traceability
Invalid contracts, missing provenance, modified dependencies/assets/source, unsupported types, resource violations and incomplete evidence fail closed in the relevant path. Fail-closed validation does not count as implementing unsupported capability. All modified original files are in lineage.
