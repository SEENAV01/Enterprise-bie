# Batch004 — bounded delivery metric API and integration

This is a local Section17 package, not the complete canonical repository and not accepted BIE software. Do not extract the outer master onto GitHub/main. Preserve current work and reconcile only inventoried owned paths against an exact checkout in a separate integration operation. No GitHub action was performed here. Task028 remains paused.

## Runtime and exact evidence
Tested: Python3.13.5, TypeScript5.8.3 (Node22.16.0), FFmpeg/FFprobe7.1.5 on Linux. Python code uses the standard library. Actual collector tests also require `tsc`, `ffmpeg`, `ffprobe` on PATH. No provider/API key is used. Other versions are not certified; commands fail closed on missing tools. Open gates and media resource bounds are in GAP_LEDGER and per-task specs.

## Dispatch compatibility
`MODULES` remains the historical six-metric roster intentionally, so old frozen suites do not silently change. New code should deliberately opt into `ALL_MODULES` (16) or `BATCH004_MODULES` (10). The `evaluate` dispatcher and CLI support all16. Existing historical TASK_RESULT files describe the candidate tested then, not current code hashes; use TASK_INTEGRATION_INDEX plus BATCH004_CHANGE_LEDGER for current identities.

## Separate trust channels
Reference and reference digest must be chosen by the evaluator. Candidate data and candidate digest bind the submitted output. Compiler/media/build observations must be captured by the evaluator, never supplied from an untrusted HTTP request as though verified. Collector receipts are self-digested consistency records, not signatures. A forged JSON record with a recomputed hash is not authenticated. The local store implements campaign reference/code pins and anti-repeat/integrity controls; it does not supply production identity, worker isolation or off-host anchoring. Run collectors only in a controlled environment, never as a public code-execution service. Compiler profiles emit bytes without executing candidate source.

```python
from bie.evaluation.benchmarks.metrics import evaluate
from bie.evaluation.benchmarks.models import digest
result = evaluate(task_id, trusted_reference, candidate,
    expected_reference_sha256=digest(trusted_reference),
    expected_candidate_sha256=digest(candidate),
    source_artifacts=trusted_collector_observations)
```

A missing/invalid required datum is not a skipped success. The persistent API records BLOCKED with no measured score. Positive unit coverage can coexist with FAIL for extra defects. Always inspect status, outcome and defects; no current result authorizes release.

## Runnable evidence workflows
Use new output directories OUTSIDE the immutable package. From combined_source:
```bash
python -B tools/verify_section17_package.py verify .
python -B tools/run_section17_tests.py --output-dir /tmp/bie-s17-tests-new
python -B tools/run_section17_batch004_diagnostics.py --output-dir /tmp/bie-s17-diagnostics-new
python -B tools/run_section17_batch004_collectors.py --output-dir /tmp/bie-s17-collectors-new
python -B tools/run_section17_batch004_fault_controls.py --output-dir /tmp/bie-s17-faults-new
python -B -m bie.evaluation.benchmarks.metrics --help
```
The first new diagnostic replays60 captured/controlled scenarios through SQLite,10PASS/44FAIL/6BLOCKED. It does not rerun60compilers. The collector workflow actually invokes5compilers (two valid language profiles, two invalid programs, one repeated Python build), fully decodes12video frames, samples3RGB frames, blocks corrupt input and persists4actual observation-bound metric evaluations. It is NOT native BIE/Remotion. Read each generated COMMAND, receipt and result, not only the summary.

## Golden/reference scope
Example sources and tiny media are authored; no real textbook is used. Reference thresholds need independent review/calibration and held-out coverage. Pedagogy/director/animation are metadata/sampled-trace diagnostics. Frame comparison is exact RGB diagnostics, not aesthetic quality. Accessibility is a partial static check, not certification. Game learning is authored response arithmetic, not evidence from learners. Reproducibility is exact bytes for this environment and scoped Python build, not cross-platform BIE.

## Preservation
Atomic runtime snapshots include the same code/test/tool inventory as the combined source. They deliberately include dependencies and tests; do not add repeated selected tests to the total. Old atomic archives and master archives remain byte-identical. Package manifests bind all extracted files except the manifest itself; the external receipt binds the final ZIP hash. A ZIP cannot contain its own final SHA256.
