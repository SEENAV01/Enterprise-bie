# BIE-EVAL-GEO-002 — maps

## Original position and local status
Section17, original position 21 of50, Batch003. SCOPED_LOCAL_IMPLEMENTATION_VERIFIED; full original capability, native integration and enterprise acceptance are NOT closed.

## Observable behavior
Printed map length/area scale, signed DMS coordinates, spherical distance and grid bearings.

## Exact bounded contract
`scale_distance`: `map_length {value,unit}` and positive `scale_denominator`; length units mm/cm/m/km. Ground metres = map metres times scale.
`scale_area`: map_area (mm2/cm2/m2); ground area = map area times scale squared.
`dms`: axis latitude/longitude; integer degrees/minutes, exact seconds; corresponding N/S or E/W hemisphere; limits 90/180, minutes/seconds <60. Negative degree entry is not combined with a hemisphere.
`spherical_distance`: two numeric degree coordinate objects and positive caller-supplied sphere radius. Haversine shortest spherical arc, antimeridian-safe; outputs floats with declared comparison tolerances.
`planar_bearing`: signed east/north displacement; clockwise angle from grid north, atan2(east,north); zero vector rejected.

The complete concrete input/output or trusted-reference/candidate examples are in `CONTRACT_EXAMPLES.json`. The implementation is `bie/evaluation/benchmarks/domains/maps.py`. Public JSON is strict: unknown/missing fields, invalid types, bool-as-number, NaN/infinity, duplicate IDs and oversized/deep objects are rejected. Rational scalar strings follow inherited integer or p/q grammar (for example `5463/20`); decimal JSON numbers are permitted, quoted decimal strings are not. Rational values are exact, bounded in magnitude and bit length. Native Python objects and executable expression strings are never evaluated.

## What is not implemented by this profile
No actual map, raster, projection, image/OCR, ellipsoidal geodesic, changing scale or routing interpretation. Printed-scale and supplied-sphere assumptions must be true upstream.

## Source and reference custody
All new fixtures are AUTHORED_DIAGNOSTIC / DEVELOPMENT, not golden or held-out. Public fixtures and expected values are intentionally visible for development, never a valid secret test set. Domain references are consultation links with original authored derivations, not copied textbooks or source-content rights grants. A hash pins bytes, not factual truth, independent approval or provenance authenticity. `metadata/section17/BATCH003_REFERENCE_CATALOG.json` retains actual source links and limitations.

## Executed selected tests
22 distinct selected methods passed in the 749-method cumulative run; method IDs are in this task's `TEST_RESULT.json` and `TEST_RESULT.txt`. They are a subset, not extra passes. Additional shared tests cover real CLI execution, candidate/reference hashes, SQLite persistence, retry controls, corruption, symlink preflight, concurrency, deterministic output, fixture regeneration and prior regressions. Final master verification additionally records independent extraction and execution of this atomic ZIP.

```bash
python -B tools/run_section17_tests.py --pattern test_geo_002.py --output-dir ../BIE-EVAL-GEO-002-new-tests
```
Use a new directory outside the immutable source. Keep prerequisite code, helpers and data in place. Source preimages and actual intermediate failure receipts are retained; do not run preimages as current code.

## Ownership and integration
Direct task dependencies: BIE-EVAL-REG-004, BIE-EVAL-BIO-001.
Owned implementation/test/fixture paths: `bie/evaluation/benchmarks/domains/maps.py`, `bie/evaluation/benchmarks/data/BIE-EVAL-GEO-002.json`, `tests/section17/test_geo_002.py`.
Shared wiring and batch tools are separately recorded in TASK_INTEGRATION_INDEX.json and BATCH003_CHANGE_LEDGER.json. Dependency runtime snapshots inside atomic ZIPs are support, not ten independent ownership claims. No blind overlay onto canonical main. Stop on a differing pre-existing owned path, review consumers and run canonical tests before adoption.

## Unclosed gates
No real-book/native BIE adapter, rendered video/frame/audio, game runtime, measured learner outcome, independently reviewed golden corpus or release authorization is supplied. Full-section audit/hardening/re-audit and original tasks31–50 remain open. Task028 in the separate app workflow remains paused (distinct from original Section17 task position28). No GitHub write or canonical continuation change occurred.
