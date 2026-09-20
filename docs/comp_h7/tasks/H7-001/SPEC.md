# BIE-COMP-H7-001 — Asset-backed dynamic layout repair

Parent: BIE-COMP-H6-005. Finding: R01.

## Required behavior
Pass verified narration assets through candidate validation and publication; check dynamic captions/state on every frame; no content/timing changes. Normalize local MP3/FLAC/Vorbis/Opus/PCM in a kernel-isolated decoder to existing verified WAV contracts; explicit sample-offset mixing rejects clipping and preserves an input/output transformation manifest.

## Execution and boundaries
This task's implementation is part of the cumulative H7 integration. Restore all eight ordered deltas before executing task suites; intermediate delta trees are assembly states, not standalone runnable applications.

```bash
PYTHONPATH=app:. python -m unittest tests.compiler.test_comp_h7_001 tests.compiler.test_comp_h7_001_audio -v
```

Targeted suite: 35 tests. Full release/package evidence is externally bound to the final integrated ZIP. Real Remotion and browser sandbox execution remain blocked; the local browser bridge has explicit API doubles and cannot authorize a production render. See `docs/COMP_H7_REAUDIT.md` for exact unclosed broader findings. Product accepted: false.

## Failure and traceability
Invalid contracts, missing provenance, modified dependencies/assets/source, unsupported types, resource violations and incomplete evidence fail closed in the relevant path. Fail-closed validation does not count as implementing unsupported capability. All modified original files are in lineage.
