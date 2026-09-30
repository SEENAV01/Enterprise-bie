# BIE-EVAL-METRIC-013 — Frame quality

Original Section17 position 37; Batch004. **Scoped local implementation; original capability, section and product NOT accepted.**

## Behavior
Actual decoded RGB samples, strict base64/byte/hash validation, mean absolute channel error, black-pixel ratio, channel range and required motion pairs.

## Trust and input contract
The evaluator, not the candidate, selects the reference, its exact digest, evaluator code and thresholds. `CONTRACT.json` records the top-level contract; the named source module enforces nested records, allowed values and finite bounds. `EXAMPLE_INPUT.json` and `EXAMPLE_OUTPUT.json` are an actual evaluated positive pair. Every required reference item remains in the scoring denominator; invalid extras may cause FAIL/BLOCKED even when covered units have full credit. Never authorize release from a numeric score alone. Missing or malformed references/evidence raise typed errors; `MetricRunStore` persists BLOCKED instead of pretending a valid score.

For compiler/media/pixel/build evidence, `source_artifacts` must come from evaluator-controlled collectors. A self-digested observation proves internal consistency only; copying a candidate-provided JSON object into that channel is prohibited by the integration contract, not prevented by cryptographic authentication in this local library.

## Implementation and dependencies
Owned code: `bie/evaluation/benchmarks/metrics/frame_quality.py`. Fixture: `bie/evaluation/benchmarks/metrics/fixtures/BIE-EVAL-METRIC-013.json`. Selected tests: `tests/section17/test_metric_013.py`. Direct logical dependencies: BIE-EVAL-METRIC-001, BIE-EVAL-METRIC-012. Shared validation, collectors, dispatch and persistent store are inventoried in TASK_INTEGRATION_INDEX. Runtime snapshots in atomics include dependencies; do not blindly overlay them on a repository.

## Tests and controls
Six authored diagnostic fixtures plus ten focused methods = 16 selected distinct methods, all part of the cumulative 962-method suite. Negative coverage includes: Altered RGB payload/hash; Black/frozen samples; Missing reference sample; Wrong dimensions/pixel errors. Shared integration/security/actual-tool tests are additional distinct methods in the cumulative suite, not multiplied per atomic. Initial failure and repair records remain under evidence/section17/batch004/audit.

## Limits and acceptance gates
Small authored pixel references are diagnostics, not subjective/perceptual aesthetics, full-video inspection, text legibility or scientific figure correctness.
Independent rubric calibration, real-book/native integration, human review and downstream release gates remain OPEN. `release_gate_eligible`, native/golden and product acceptance flags are not granted by this task.

## Sources and provenance
See `metadata/section17/BATCH004_REFERENCE_CATALOG.json`. These are authored diagnostic references; `basis_sha256` hashes the reference payload, not this Markdown file or an external publication. Package manifests bind actual file bytes.

## Re-run
From combined_source (or an atomic's runtime directory):
```bash
python -B tools/run_section17_tests.py --pattern test_metric_013.py --output-dir /tmp/BIE-EVAL-METRIC-013-new-test-evidence
```
Use a new, private output directory outside the immutable package.
