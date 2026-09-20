# BIE COMP — Hardening H1 cumulative workspace

Continues original COMP Batch 009 (QA-005) without restarting the architecture.

Start with `docs/COMP_H1_SPEC.md`, `docs/COMP_H1_REAUDIT.md`, `BATCH_MANIFEST.json` and `CONTINUATION.json`. The H1 registry is audit-derived, not an invented continuation of the original QA numbering. Section IN PROGRESS; product NOT ACCEPTED.

```bash
PYTHONPATH=app:. python -m unittest discover -s tests -v
python scripts/run_compiler_qa.py --output /tmp/bie-h1-new-benchmark
python scripts/compile_scene_checked.py examples/comp_h1/signed_chart_scene.json /tmp/bie-h1-project
python scripts/validate_checked_remotion.py /tmp/bie-h1-project
```

The new checked harness is the current guarded path. The retained earlier technical-fixture generator/validator are diagnostic legacy scripts and do not produce CHECKED_SCENE provenance; do not bypass the new gate to run them.

No default command installs npm dependencies, writes GitHub, grants real-book acceptance or claims a rendered lesson. The benchmark deliberately exits 2 when source expectations match but dependencies/full compilation are blocked. Explicit `--install` is available only on the checked validation harness. Actual rendering still requires the real pinned environment.

Original changed files are preserved below `lineage/batch_009`, alongside all parent member hashes. Old fixture/golden bytes remain untouched; H1 corpus and expected-output changes are separately governed. Master backup also embeds the unchanged Batch 009 master.
