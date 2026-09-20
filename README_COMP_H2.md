# Compiler hardening H2 — cumulative continuation

This is the source continuation of H1, not a new BIE implementation. Compiler identity: `1.2.0-comp-h2`. Five audit-derived tasks cover bounded equation typesetting, three analytic simulation models, six generic motion actions, two declared geographic projections, and checked adoption/evidence. Read `docs/COMP_H2_SPEC.md` before integrating.

Quick verification:

```bash
PYTHONPATH=app:. python -m unittest discover -s tests -v
python scripts/run_compiler_qa.py --output /tmp/bie-h2-benchmark-new --runs 3
python scripts/validate_comp_h2_browser.py --output /tmp/bie-h2-browser-new
python scripts/compile_scene_checked.py examples/comp_h2/combined_technical_scene.json /tmp/bie-h2-project-new
python scripts/validate_checked_remotion.py /tmp/bie-h2-project-new
```

Use fresh output directories. Python compiler and test dependencies are separately pinned in `requirements-comp-h2.txt` and `requirements-comp-h2-test.txt`. Node/tsc, Chromium and FFmpeg/ffprobe are external executables; see the recorded environment. No fonts are bundled.

The 59-case synthetic benchmark has development-reviewed frozen expectations and cannot rebase itself. The 11-case browser harness executes generated component functions through explicitly named React/Remotion hook doubles and paints the host tree in actual Chromium. It is **not** actual React/Remotion rendering. The final browser evidence is `validation/comp_h2/browser_run_003`; earlier runs retain findings and corrections. Source PASS and browser-component PASS do not mark full project compilation, real books or learning quality accepted.

The actual real-render path remains fail-closed on missing pinned dependencies. No GitHub write or section exit has occurred. Continue with the grounded residuals in `docs/COMP_H2_REAUDIT.md`; do not skip to another section merely because this hardening batch passed local tests.

Original H1 member hashes and changed original bytes are in `lineage/hardening_h1`. Earlier lineage remains intact. The original H1 master backup is embedded unchanged in the separate H2 master backup.
