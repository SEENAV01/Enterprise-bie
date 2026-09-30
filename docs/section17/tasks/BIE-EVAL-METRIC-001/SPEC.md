# BIE-EVAL-METRIC-001 — grounding metric

## Original position and local status
Section17, original position 25 of50, Batch003. SCOPED_LOCAL_IMPLEMENTATION_VERIFIED; full original capability, native integration and enterprise acceptance are NOT closed.

## Observable behavior
Candidate-bound weighted proposition/citation checking against exact captured authored source text.

## Exact bounded contract
Reference payload: sources {id,text_sha256,locator}, claims {id,weight,proposition,supports}. Candidate: claims {id,proposition,citations}. A typed proposition has subject,predicate,object; IDs and scalar types are strict.
Actual source_artifacts text must exactly match the trusted source roster and UTF-8 hashes. Spans use Python/Unicode codepoint indices, not byte offsets or grapheme clusters. Reference spans have expected span SHA256. Candidate citations must all match annotated supports; at least one annotated support is required per present claim.
Each trusted claim earns all or zero declared weight; missing, changed, uncited or unannotated claims fail. Duplicate citations/unknown claims or sources are blocked rather than discarded. Grounding is measured from artifacts, not a candidate-owned PASS assertion.

The complete concrete input/output or trusted-reference/candidate examples are in `CONTRACT_EXAMPLES.json`. The implementation is `bie/evaluation/benchmarks/metrics/grounding.py`. Public JSON is strict: unknown/missing fields, invalid types, bool-as-number, NaN/infinity, duplicate IDs and oversized/deep objects are rejected. Rational scalar strings follow inherited integer or p/q grammar (for example `5463/20`); decimal JSON numbers are permitted, quoted decimal strings are not. Rational values are exact, bounded in magnitude and bit length. Native Python objects and executable expression strings are never evaluated.

## What is not implemented by this profile
Exact span binding does not establish entailment, truth or licensing. Proposition-to-source support is curated, not NLP-inferred. Original authored text is bundled only in fixture artifacts. Independent source review and native PDF/text span adaptation remain open.

## Source and reference custody
All new fixtures are AUTHORED_DIAGNOSTIC / DEVELOPMENT, not golden or held-out. Public fixtures and expected values are intentionally visible for development, never a valid secret test set. Domain references are consultation links with original authored derivations, not copied textbooks or source-content rights grants. A hash pins bytes, not factual truth, independent approval or provenance authenticity. `metadata/section17/BATCH003_REFERENCE_CATALOG.json` retains actual source links and limitations.

## Executed selected tests
20 distinct selected methods passed in the 749-method cumulative run; method IDs are in this task's `TEST_RESULT.json` and `TEST_RESULT.txt`. They are a subset, not extra passes. Additional shared tests cover real CLI execution, candidate/reference hashes, SQLite persistence, retry controls, corruption, symlink preflight, concurrency, deterministic output, fixture regeneration and prior regressions. Final master verification additionally records independent extraction and execution of this atomic ZIP.

```bash
python -B tools/run_section17_tests.py --pattern test_metric_001.py --output-dir ../BIE-EVAL-METRIC-001-new-tests
```
Use a new directory outside the immutable source. Keep prerequisite code, helpers and data in place. Source preimages and actual intermediate failure receipts are retained; do not run preimages as current code.

## Ownership and integration
Direct task dependencies: BIE-EVAL-REG-004, BIE-EVAL-BIO-001.
Owned implementation/test/fixture paths: `bie/evaluation/benchmarks/metrics/grounding.py`, `bie/evaluation/benchmarks/metrics/fixtures/BIE-EVAL-METRIC-001.json`, `tests/section17/test_metric_001.py`, `bie/evaluation/benchmarks/metrics/__init__.py`, `bie/evaluation/benchmarks/metrics/common.py`, `bie/evaluation/benchmarks/metrics/service.py`, `bie/evaluation/benchmarks/metrics/__main__.py`.
Shared wiring and batch tools are separately recorded in TASK_INTEGRATION_INDEX.json and BATCH003_CHANGE_LEDGER.json. Dependency runtime snapshots inside atomic ZIPs are support, not ten independent ownership claims. No blind overlay onto canonical main. Stop on a differing pre-existing owned path, review consumers and run canonical tests before adoption.

## Unclosed gates
No real-book/native BIE adapter, rendered video/frame/audio, game runtime, measured learner outcome, independently reviewed golden corpus or release authorization is supplied. Full-section audit/hardening/re-audit and original tasks31–50 remain open. Task028 in the separate app workflow remains paused (distinct from original Section17 task position28). No GitHub write or canonical continuation change occurred.

## Shared candidate-driven metric API
`metrics.evaluate(metric_id, reference, candidate, expected_reference_sha256=..., expected_candidate_sha256=..., source_artifacts=...)` checks caller-pinned hashes before measurement. The reference envelope fixes schema_version, metric_id, rubric_id, semantic version, reference_owner_id, evidence_grade, nonempty source_refs and payload. Hashes supplied by the same untrusted candidate are not an independent trust boundary: production must choose/pin references externally and isolate this private evaluator.

Result contains MEASURED status, score_exact, earned_weight, total_weight, trusted unit denominator, item defects, outcome, reference/candidate/evaluator code hashes and explicit false native/release/product acceptance flags. Missing candidate items stay in the denominator. Extra false work can yield score1 but outcome FAIL; downstream must not authorize from score alone. Invalid input/source evidence raises BenchmarkError. MetricRunStore persists accepted submissions that fail evidence checks as BLOCKED receipts with no score. It pins reference and evaluator code per campaign/metric and rejects duplicate candidate attempts in that campaign. Cross-campaign identity/custody must be governed externally.

CLI (run from combined_source, all outputs new and outside immutable package):
```bash
python -B -m bie.evaluation.benchmarks.metrics --metric METRIC_ID --reference REFERENCE.json --candidate CANDIDATE.json --reference-sha PINNED_REFERENCE_SHA --candidate-sha CANDIDATE_SHA --source-artifacts ARTIFACTS.json --database ../runs.sqlite3 --run-id RUN_ID --campaign-id CAMPAIGN_ID --output-dir ../new-result
```
For metrics other than grounding, omit source-artifacts or supply an empty map. Exit0 is a local measured PASS, exit1 a measured FAIL, exit2 BLOCKED. Both pass and fail outputs persist; fixture replay is available through `tools/run_section17_batch003_metric_diagnostics.py`.

SQLite is a local trusted-directory implementation, not an authenticated hosted service. Receipt hashes catch accidental/uncoordinated tampering, not an attacker replacing both JSON and hash. Symlink/nonregular-path preflight is not a race-proof filesystem sandbox. Production signatures, off-host anchoring, secure worker isolation, source licensing and human/rater calibration remain open.
