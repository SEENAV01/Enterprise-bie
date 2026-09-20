# BIE-COMP-H7-004 — Operational Linux isolation

Parent: BIE-COMP-H6-005. Finding: R03.

## Required behavior
Private user/mount/PID/network namespaces; read-only system/engine mounts, private writable workspace, no-new-privileges/syscall restrictions, resource limits and lock-based concurrency. Adopt the same kernel worker for checked-source Mathtext and audio decoding. Browser procfs profile remains distinct from the no-proc compiler profile.

## Execution and boundaries
This task's implementation is part of the cumulative H7 integration. Restore all eight ordered deltas before executing task suites; intermediate delta trees are assembly states, not standalone runnable applications.

```bash
PYTHONPATH=app:. python -m unittest tests.compiler.test_comp_h7_004 -v
```

Targeted suite: 22 tests. Full release/package evidence is externally bound to the final integrated ZIP. Real Remotion and browser sandbox execution remain blocked; the local browser bridge has explicit API doubles and cannot authorize a production render. See `docs/COMP_H7_REAUDIT.md` for exact unclosed broader findings. Product accepted: false.

## Failure and traceability
Invalid contracts, missing provenance, modified dependencies/assets/source, unsupported types, resource violations and incomplete evidence fail closed in the relevant path. Fail-closed validation does not count as implementing unsupported capability. All modified original files are in lineage.
