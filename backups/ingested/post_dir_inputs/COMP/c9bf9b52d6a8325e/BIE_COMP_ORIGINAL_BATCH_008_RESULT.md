# BIE COMP Original Batch 008 — BUILD-007..010

**IMPLEMENTED — LOCAL TESTS PASS — ACTUAL REMOTION EXECUTION BLOCKED — NOT ACCEPTED**

## Delivered capabilities

| Task | Capability | Atomic tests |
|---|---|---:|
| BIE-COMP-BUILD-007 | Smoke render | 21 |
| BIE-COMP-BUILD-008 | Full render | 19 |
| BIE-COMP-BUILD-009 | Render logs and bounded process lifecycle | 22 |
| BIE-COMP-BUILD-010 | Artifact hashing and integrity verification | 19 |

The render path integrates explicit frame planning, local installed CLI invocation,
source/toolchain identity, staged outputs, decoded-media checks, exclusive publication,
structured logs, cancellation/timeouts, evidence sealing and content hashes. Shared
runtime supports the four tasks without replacing any prior implementation module.

## Executed verification

- Uploaded parent embedded workspace: byte-identical; **11/11** backup checksums verified.
- Uploaded source archive: `d752c2d8192b72fcac169e662dd5cccca3b417eb5140678d2b546f5eef113f25`.
- Restored baseline: **657/657 PASS**.
- New atomic tests: **81/81 PASS**.
- Cross-task integration tests: **13/13 PASS**.
- Total new tests: **94**; cumulative DSL + COMP: **751/751 PASS**.
- Failures/errors/skips in final suites: **0/0/0**.
- Original Python source/test files preserved byte-for-byte: **272**; modified: **0**.
- Original workspace members accounted for: **293**. Original root metadata is preserved under `lineage/` before continuation metadata is advanced.
- The final suite scope is DSL + COMP, **not** the entire canonical enterprise monorepo.

The uploaded files are a later Batch 007 document revision than the recovered library
reports: **657/35** baseline/corresponding atomic counts, not **656/34**. The uploaded
source bytes and the actual rerun govern this continuation.

## Execution truth boundary

Real execution performed: POSIX child processes, failure/timeout/cancellation handling,
process-group teardown, bounded capture, real FFmpeg-generated **technical test patterns**,
real ffprobe frame decoding, and actual file/log/hash verification. Media integration
uses an explicitly injected renderer and is labelled `INJECTED_TEST_RUNNER` throughout.

The unchanged original BIE React emitters generated a separate technical fixture. An
actual npm lookup failed with **EAI_AGAIN** for `registry.npmjs.org`. Remotion dependencies
were not installed. The optional real validation entry point also demonstrated a
fail-closed missing-local-tsc response without proceeding to rendering.

Therefore **real Remotion composition discovery, smoke rendering, full rendering,
rendered-frame inspection, and real-book end-to-end acceptance are NOT RUN**. No
FFmpeg test-pattern video is claimed to be a Remotion output or a BIE lesson. The new
render execution backend still needs empirical validation with installed Remotion.

All top-level receipts keep `accepted=false`. Artifact hashes prove observed byte
integrity, not educational correctness or cross-machine reproducibility. This POSIX
process adapter is not a multi-tenant execution sandbox. Full security/asset/network,
audio, learning-quality, game-runtime and enterprise acceptance gates remain open.

## Reproducible run paths

Cumulative tests: `PYTHONPATH=app python -m unittest discover -s tests -v`.

Generic existing-project render: `python scripts/run_comp_render.py request.json --mode full`.

Opt-in actual technical validation in a dependency-enabled environment:
`python scripts/validate_real_remotion.py validation/comp_build_008/real_remotion_project --install --browser /usr/bin/chromium`.
This runs dependency installation, strict TypeScript, inherited lint/static analysis,
real composition discovery, smoke/full render and evidence verification, stopping at
the first failure. It does not patch the emitted source or substitute a test runner.

## Section and repository state

COMP remains **IN_PROGRESS**. No section-exit or product-acceptance claim is made.
No GitHub file, branch or commit was created or changed in this batch.
The next original registry tasks are **BIE-COMP-QA-001..005**: compile diagnostics mapping,
capability fallback QA, deterministic output testing, generated-code regression and
multidomain compile benchmarks. Carry the actual-Remotion execution block into that
work. Original task completion must still be followed by capability audit, justified
hardening, regression and re-audit before any section exit.

## Packaging evidence

The delivery includes four self-contained atomic ZIPs, a cumulative DSL + COMP source
ZIP, prior immutable master backup, result/continuation/manifest files, test receipts,
actual dependency-failure evidence, and checksums. Fresh-extraction execution and final
master-byte verification are recorded in the master backup's `verification/` directory.
