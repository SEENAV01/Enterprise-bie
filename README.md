# My Book Intelligence Engine

Continuation of the existing enterprise BIE repository, not a new architecture or product release.

Working Python source lives in `bie/`, following `schemas/canonical-monorepo.json`. Existing Prerequisite, Math, Document, Knowledge, model gateway and infrastructure implementations are retained. Supported `app.bie.*` imports resolve to the same canonical module identities.

## Current checkpoint

Reasoning implementation includes **RE-SPATIAL-003/004 and RE-TEMP-001/002/003**. See `task_registry/continuation.json` and `docs/tasks/`.

- 796 original archives and 12,439 historical member files accounted for.
- All 273 Assembly-001 archive hashes and 2,450 member records match the recovered originals.
- 1,654 passing tests: 1,551 restored regressions, 78 task tests, 13 integration/contract tests and 12 assembly guards.
- IMPLEMENTED, **NOT ACCEPTED**. Real-book reasoning and rendered-video/playable-game acceptance remain pending.

## Run

Python 3.11+; validated on Python 3.12.14. The current enterprise Python distribution needs no third-party runtime packages.

```bash
python scripts/integrated_check.py
python -m pip install .
```

The packaging version denotes this canonical distribution, not a reset of historical product versions.

## Preservation and development

`bie/` is the development source. `tests/` contains normalized working tests. `batches/`, `historical/` and `backups/` retain original bytes and evidence; they are not imported by the production package.

`manifests/lossless_migration.csv` documents every original file. The 390 older M-series/historical packages remain preserved for governed characterization and later wiring; this migration does not claim all legacy features are already integrated into the enterprise pipeline.

See `docs/adr/ADR-canonical-assembly-002.md`, `docs/GITHUB_SYNC.md` and `docs/REASONING_BATCH_SPATIAL_TEMPORAL.md` for scope and evidence.
