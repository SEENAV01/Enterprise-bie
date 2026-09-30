# BIE-EVAL-GEO-003 — climate systems

## Original position and local status
Section17, original position 22 of50, Batch003. SCOPED_LOCAL_IMPLEMENTATION_VERIFIED; full original capability, native integration and enterprise acceptance are NOT closed.

## Observable behavior
Declared global energy/water budgets, 30-year anomaly arithmetic, area weighting and feedback polarity.

## Exact bounded contract
`planetary_budget`: S>0, albedo in [0,1], emissivity in (0,1]; absorbed = S(1-a)/4, reflected = Sa/4; radiating temperature from absorbed/(emissivity*sigma) to power 1/4. Sigma is 5.670374419e-8 in declared SI units.
`water_budget`: precipitation minus evapotranspiration minus runoff in mm, allowing signed storage change; mm/cm/m inputs.
`temperature_anomaly`: exactly 30 distinct consecutive supplied annual means matching baseline_start..end, years 1..9999. Equal-year mean only. Absolute input temperature units degC/K; converted before anomaly. Below absolute zero rejected.
`area_weighted_temperature`: unique declared nonoverlapping regions and strictly positive km2 weights.
`feedback_loop`: 2..32 signed edges forming exactly one simple closed cycle; sign product positive means reinforcing, negative means balancing.

The complete concrete input/output or trusted-reference/candidate examples are in `CONTRACT_EXAMPLES.json`. The implementation is `bie/evaluation/benchmarks/domains/climate.py`. Public JSON is strict: unknown/missing fields, invalid types, bool-as-number, NaN/infinity, duplicate IDs and oversized/deep objects are rejected. Rational scalar strings follow inherited integer or p/q grammar (for example `5463/20`); decimal JSON numbers are permitted, quoted decimal strings are not. Rational values are exact, bounded in magnitude and bit length. Native Python objects and executable expression strings are never evaluated.

## What is not implemented by this profile
Effective radiating temperature is not observed surface temperature. No climate forecast, empirical feedback attribution, station homogenization, missing-year imputation or certified climate-normal computation.

## Source and reference custody
All new fixtures are AUTHORED_DIAGNOSTIC / DEVELOPMENT, not golden or held-out. Public fixtures and expected values are intentionally visible for development, never a valid secret test set. Domain references are consultation links with original authored derivations, not copied textbooks or source-content rights grants. A hash pins bytes, not factual truth, independent approval or provenance authenticity. `metadata/section17/BATCH003_REFERENCE_CATALOG.json` retains actual source links and limitations.

## Executed selected tests
22 distinct selected methods passed in the 749-method cumulative run; method IDs are in this task's `TEST_RESULT.json` and `TEST_RESULT.txt`. They are a subset, not extra passes. Additional shared tests cover real CLI execution, candidate/reference hashes, SQLite persistence, retry controls, corruption, symlink preflight, concurrency, deterministic output, fixture regeneration and prior regressions. Final master verification additionally records independent extraction and execution of this atomic ZIP.

```bash
python -B tools/run_section17_tests.py --pattern test_geo_003.py --output-dir ../BIE-EVAL-GEO-003-new-tests
```
Use a new directory outside the immutable source. Keep prerequisite code, helpers and data in place. Source preimages and actual intermediate failure receipts are retained; do not run preimages as current code.

## Ownership and integration
Direct task dependencies: BIE-EVAL-REG-004, BIE-EVAL-BIO-001.
Owned implementation/test/fixture paths: `bie/evaluation/benchmarks/domains/climate.py`, `bie/evaluation/benchmarks/data/BIE-EVAL-GEO-003.json`, `tests/section17/test_geo_003.py`.
Shared wiring and batch tools are separately recorded in TASK_INTEGRATION_INDEX.json and BATCH003_CHANGE_LEDGER.json. Dependency runtime snapshots inside atomic ZIPs are support, not ten independent ownership claims. No blind overlay onto canonical main. Stop on a differing pre-existing owned path, review consumers and run canonical tests before adoption.

## Unclosed gates
No real-book/native BIE adapter, rendered video/frame/audio, game runtime, measured learner outcome, independently reviewed golden corpus or release authorization is supplied. Full-section audit/hardening/re-audit and original tasks31–50 remain open. Task028 in the separate app workflow remains paused (distinct from original Section17 task position28). No GitHub write or canonical continuation change occurred.
