# BIE COMP Original Batch 008 — BUILD-007..010

This is a continuation of the uploaded Batch 007. It includes all prior cumulative
DSL + COMP source/tests plus the four new compiler-build capabilities. It is not a
restart, a new architecture, a canonical GitHub integration, or a product release.

## Run the cumulative regression

From this extracted workspace on POSIX, with Python, npm, tsc, FFmpeg and ffprobe available:

```bash
PYTHONPATH=app python -m unittest discover -s tests -v
```

Some inherited tests require npm/tsc. New media/lifecycle tests require FFmpeg/ffprobe
and POSIX process groups. Missing real tools are not silently replaced by simulated
passes. The test helpers explicitly label injected renderer behavior.

## Execute a generated project

`python scripts/run_comp_render.py request.json --mode smoke --frame-count 12`

`python scripts/run_comp_render.py request.json --mode full`

Use different `run_id` and `output_path` values for separate attempts. The JSON uses
`RenderRequest` fields; its `composition` uses `CompositionDescriptor` fields.
Relative `workspace` is resolved beside the request JSON. The script requires existing,
locally installed, package-lock-matched Remotion dependencies. No package install occurs
inside render functions. Example requests are in the generated technical fixture.

## Close the actual-Remotion execution gap in an enabled environment

A generated technical fixture is included at:
`validation/comp_build_008/real_remotion_project/`.

```bash
python scripts/validate_real_remotion.py \
  validation/comp_build_008/real_remotion_project \
  --install --browser /usr/bin/chromium
```

This explicitly permits npm install (or `npm ci` when a lock already exists), then runs
strict TypeScript, inherited lint/static-analysis gates, real CLI composition discovery,
smoke, full rendering, and evidence verification. A failed stage stops later stages.
It does not patch generated source behind the compiler, use a fixture runner, or grant
product acceptance. The browser path is operator-configurable.

The request files and unmodified emitter output in the fixture are technical validation
material, not a book-to-video output. Registry access in this session failed with
`EAI_AGAIN`; see the retained receipt. Do not describe the fixture as successfully
compiled/rendered before executing this path and inspecting its evidence.

## Evidence and lineage

- `docs/BUILD_007_010_SPEC.md`: contracts, scope, boundaries and next original tasks.
- `validation/comp_build_008/`: baseline/new/cumulative execution logs and media fixtures.
- `lineage/`: original metadata and byte-preservation map.
- `CONTINUATION.json`: implementation checkpoint and outstanding empirical gates.
- Atomic ZIPs: task-specific metadata/spec/test evidence with all required source.
- Master backup: cumulative source, four atomic ZIPs, prior master bytes and checksums.

Every new receipt remains `accepted=false`. COMP remains IN_PROGRESS. Next original
family: COMP-QA-001..005, with the actual-Remotion execution block explicitly carried forward.
