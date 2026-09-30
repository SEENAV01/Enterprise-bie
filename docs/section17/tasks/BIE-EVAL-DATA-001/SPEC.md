# BIE-EVAL-DATA-001 — tables/charts

## Original position and local status
Section17, original position 24 of50, Batch003. SCOPED_LOCAL_IMPLEMENTATION_VERIFIED; full original capability, native integration and enterprise acceptance are NOT closed.

## Observable behavior
Exact table arithmetic and structured cell-to-chart fidelity with explicit missing data and axes.

## Exact bounded contract
`summary`: unique row IDs, rational values or null, missing_policy reject/exclude_explicit; sum, mean, odd/even median, observed/missing counts and excluded IDs; all missing rejected.
`percent_change`: positive baseline, nonnegative final value; 100(after-before)/before.
`weighted_mean`: unique rows with nonnegative weight and signed rational values; total weight strictly positive.
`chart_fidelity`: source_rows vs chart_points joined by ID; explicit source/chart units, bar/line/scatter type and bounded linear/log y_axis. Mismatched unit labels are not implicitly converted. Missing/extra/wrong/out-of-axis values are defects. Zero-excluding bar axes and log scales generate separate presentation warnings.

The complete concrete input/output or trusted-reference/candidate examples are in `CONTRACT_EXAMPLES.json`. The implementation is `bie/evaluation/benchmarks/domains/tables_charts.py`. Public JSON is strict: unknown/missing fields, invalid types, bool-as-number, NaN/infinity, duplicate IDs and oversized/deep objects are rejected. Rational scalar strings follow inherited integer or p/q grammar (for example `5463/20`); decimal JSON numbers are permitted, quoted decimal strings are not. Rational values are exact, bounded in magnitude and bit length. Native Python objects and executable expression strings are never evaluated.

## What is not implemented by this profile
No PDF table extraction, raster chart interpretation, render verification or holistic visual-quality judgment. Data fidelity can pass while presentation warnings remain; neither proves good pedagogy.

## Source and reference custody
All new fixtures are AUTHORED_DIAGNOSTIC / DEVELOPMENT, not golden or held-out. Public fixtures and expected values are intentionally visible for development, never a valid secret test set. Domain references are consultation links with original authored derivations, not copied textbooks or source-content rights grants. A hash pins bytes, not factual truth, independent approval or provenance authenticity. `metadata/section17/BATCH003_REFERENCE_CATALOG.json` retains actual source links and limitations.

## Executed selected tests
22 distinct selected methods passed in the 749-method cumulative run; method IDs are in this task's `TEST_RESULT.json` and `TEST_RESULT.txt`. They are a subset, not extra passes. Additional shared tests cover real CLI execution, candidate/reference hashes, SQLite persistence, retry controls, corruption, symlink preflight, concurrency, deterministic output, fixture regeneration and prior regressions. Final master verification additionally records independent extraction and execution of this atomic ZIP.

```bash
python -B tools/run_section17_tests.py --pattern test_data_001.py --output-dir ../BIE-EVAL-DATA-001-new-tests
```
Use a new directory outside the immutable source. Keep prerequisite code, helpers and data in place. Source preimages and actual intermediate failure receipts are retained; do not run preimages as current code.

## Ownership and integration
Direct task dependencies: BIE-EVAL-REG-004, BIE-EVAL-BIO-001.
Owned implementation/test/fixture paths: `bie/evaluation/benchmarks/domains/tables_charts.py`, `bie/evaluation/benchmarks/data/BIE-EVAL-DATA-001.json`, `tests/section17/test_data_001.py`.
Shared wiring and batch tools are separately recorded in TASK_INTEGRATION_INDEX.json and BATCH003_CHANGE_LEDGER.json. Dependency runtime snapshots inside atomic ZIPs are support, not ten independent ownership claims. No blind overlay onto canonical main. Stop on a differing pre-existing owned path, review consumers and run canonical tests before adoption.

## Unclosed gates
No real-book/native BIE adapter, rendered video/frame/audio, game runtime, measured learner outcome, independently reviewed golden corpus or release authorization is supplied. Full-section audit/hardening/re-audit and original tasks31–50 remain open. Task028 in the separate app workflow remains paused (distinct from original Section17 task position28). No GitHub write or canonical continuation change occurred.
