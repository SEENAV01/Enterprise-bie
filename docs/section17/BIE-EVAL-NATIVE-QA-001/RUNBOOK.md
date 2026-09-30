# Section 17 — Native QA integration slice 001

This is a **local component-integration delivery**, not a completed Section 17,
production release, canonical application adoption, or a complete BIE repository.
There is one justified new atomic task: `BIE-EVAL-NATIVE-QA-001`.
The earlier 50 original tasks and H1–H5 are not renumbered.

## What runs

`bie.evaluation.benchmarks.native_qa.execute` calls the existing render,
frame-reference and accessibility AV metric routes on actual captured media.
It binds the exact source/game/video/support artifact bytes to a real canonical
`ReleaseCandidate`, produces an unsigned content-bound benchmark report and
invokes the **actual** `bie.qa.release_v2.ReleaseEvaluator`.
The ten QA dependency files match the Git blob identities at commit
`8b8e500bf7b83addfcecce41c3fca08563eceb41`.
The dependency snapshot is not a full repository checkout.

Three technically passing metrics do **not** establish a full benchmark: the
native evidence status is `NOT_RUN` for incomplete full-benchmark coverage.
A metric failure propagates `FAIL`; unavailable/corrupt execution propagates
`ERROR`. The canonical QA decision stays `BLOCKED`, with all 28 required gates,
no signature, no publication and no product acceptance.

## Runtime and commands

The implementation uses Python standard library code. The full retained suite
also expects approved Python packages and external tools already required by
H1–H5: Playwright with Chromium, FFmpeg/ffprobe, Node and TypeScript, etc.
These binaries/packages are **not bundled**. This POSIX custody implementation
is tested on Linux; use a governed Linux/WSL execution environment for replay.
Do not change managed browser policy to make a test pass.

From the root of the combined package (or this atomic package):

```sh
python combined_source/tools/run_section17_native_qa_tests.py --output-dir replay-tests
python combined_source/tools/run_section17_native_qa_tests.py --pattern 'test_native_qa*.py' --output-dir replay-native-tests
python combined_source/tools/run_section17_native_qa_diagnostics.py --output-dir replay-diagnostics
```

The test/diagnostic scripts explicitly locate the sibling `dependency_snapshot`.
Diagnostic fixtures are authored tiny media and placeholder source/game files,
not canonical book output. Paths provided with `--output-dir` must be fresh.

The production-shaped operator command is available without fixture generation:

```sh
export PYTHONPATH="$PWD/combined_source:$PWD/dependency_snapshot"
python -m bie.evaluation.benchmarks.native_qa \
  --candidate-bundle candidate.bundle.json --checks checks.json \
  --limits limits.json --artifact-root artifacts --as-of 1790701200 \
  --expected-candidate-digest '<trusted-candidate-digest>' \
  --expected-policy-digest '<trusted-policy-digest>' \
  --expected-checks-digest '<trusted-check-plan-digest>' \
  --output-dir fresh-run
```

The CLI returns **exit code 2** for this slice even when all three metric checks
pass, because the native release decision is BLOCKED. It writes exact report,
envelope, QA output and receipt manifest files. Caller-supplied evidence is
rejected. Trusted hashes/limits must be obtained out of band, not auto-approved
from a submitted candidate. Hashes are identity checks, not signatures.

## Preservation and package map

`combined_source/` is assembled runnable Section17 code; no atomic ZIP overlay
is necessary. `dependency_snapshot/` contains the ten pinned QA modules.
The main archive contains `history/H4_EXACT_MASTER.zip` unchanged, which itself
contains the earlier 90 atomic ZIPs and available preceding history. The ten
exact H5 atomic ZIPs and this one new atomic are separately present under
`atomics/`. Thus 101 logical atomic ZIPs are available, without duplicating all
90 at the outer level. Original H5 reports and final-check receipts are retained.

**Known gaps:** original H3 and H5 master ZIPs and some historical ancillary
records are unavailable. Recovery matched 322 of 324 published H5 inventory
files; `tools/run_section17_h5_diagnostics.py` and
`tools/run_section17_h5_fault_controls.py` are absent. No replacement is labelled
as those originals. All runtime code and all 1,875 earlier tests were recovered.
The original H5 master is NOT claimed preserved. See `RECOVERY_REPORT.json`.

Read `CONTINUATION.json`, `REPORT.md` and `CAPABILITY_AUDIT.md` before continuing.
Legacy READMEs/specs and receipts are historical evidence, not current acceptance.
The next step is canonical caller/campaign integration and actual real-book
validation in an authorized environment—not more wrappers to fill a ZIP count.
