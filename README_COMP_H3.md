# COMP Hardening H3 — cumulative continuation

Latest implemented task: `BIE-COMP-H3-005`. COMP remains IN PROGRESS / NOT ACCEPTED.
This extends the H2 source, preserving every parent archive member and exact originals for changed files.
No GitHub write occurred. Read docs/COMP_H3_SPEC.md and docs/COMP_H3_REAUDIT.md first.

## Run tests

From this extracted directory with the documented dependencies installed:

```bash
PYTHONPATH=app:. python -m unittest discover -s tests -v
PYTHONPATH=app:. python -m unittest tests.compiler.test_comp_h3_004 -v
```

A compatible Node executable, real TypeScript parser, FFmpeg/ffprobe, Python dependencies and POSIX resource limits are used by technical tests. Browser evidence additionally uses Playwright with a local Chromium executable. The exact observed local environment is recorded, not silently installed.

## Source publication and explicit reduced motion

```bash
PYTHONPATH=app:. python scripts/compile_scene_checked.py validation/comp_h3/COMBINED_TECHNICAL_SCENE.json /absolute/new-output --motion-preference reduced
PYTHONPATH=app:. python scripts/validate_checked_remotion.py /absolute/new-output --browser /usr/bin/chromium
```

The combined fixture was verified at 1280x720 using the Python API; the CLI default is 640x360. These source fixtures are technical examples, not an accepted lesson. Layout fit must be remeasured at any changed target.

The real validation command does not download dependencies by default. `--install` explicitly permits pinned dependency installation. It fails closed while dependencies are unavailable. Do not treat a source receipt, JSX test bridge, or caller-provided DOM report as real rendering.

## Repeat browser/source evidence

```bash
PYTHONPATH=app:. python scripts/validate_comp_h3_browser.py --output /absolute/new-browser-evidence --chromium /usr/bin/chromium
PYTHONPATH=app:. python scripts/run_comp_h3_source_benchmark.py --output /absolute/new-source-benchmark --runs 3
```

The browser harness executes generated TS and whole-scene wrappers with explicit React/Remotion doubles, then paints DOM in real Chromium. It measures all integer frames but saves only selected screenshots. The technical browser is launched with its sandbox disabled for local fixtures, never claimed as operational isolation. Source benchmark exit 0 means only its explicitly named SOURCE expectations matched; real compile/render is not part of that command.

The isolated math worker applies measured POSIX limits and sanitized process controls; this is not an OS/network hostile-code sandbox. Host identity hashes fonts without bundling or distributing font files.

## Reproducibility and archive integrity

`WORKSPACE_SHA256SUMS.txt` hashes all payload files except itself. Historical manifests are under lineage. Outer ZIP hashes and independently extracted test results are in the master backup's final verification and delivery-hash files. Source code is not rewritten after fresh package verification.
