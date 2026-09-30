# BIE-EVAL-CIV-001 — civics/institutions

## Original position and local status
Section17, original position 23 of50, Batch003. SCOPED_LOCAL_IMPLEMENTATION_VERIFIED; full original capability, native integration and enterprise acceptance are NOT closed.

## Observable behavior
Descriptive selected UK institution roles, ordinary two-house bill traces, and explicit fictional power tables.

## Exact bounded contract
`audit_roles`: fixed `UK_INTRO_2026-09-29` introductory reference profile; typed assertions checked for missing, unknown and mismatched values. The five role assertions and official source links are in CONTRACT_EXAMPLES.json.
`ordinary_bill_trace`: explicit `ordinary_two_house_bill` route; unique introduced/commons_agreed/lords_agreed/royal_assent events (maximum four); either house may agree first; introduction then both approvals before assent; no post-assent steps.
`fictional_competence`: explicit FICTIONAL_EDUCATIONAL_SCENARIO, unique institution IDs, unique declared powers, institution/power request; returns membership in supplied scenario.

The complete concrete input/output or trusted-reference/candidate examples are in `CONTRACT_EXAMPLES.json`. The implementation is `bie/evaluation/benchmarks/domains/civics.py`. Public JSON is strict: unknown/missing fields, invalid types, bool-as-number, NaN/infinity, duplicate IDs and oversized/deep objects are rejected. Rational scalar strings follow inherited integer or p/q grammar (for example `5463/20`); decimal JSON numbers are permitted, quoted decimal strings are not. Rational values are exact, bounded in magnitude and bit length. Native Python objects and executable expression strings are never evaluated.

## What is not implemented by this profile
Not comprehensive constitutional law; special bill routes excluded. The UK profile is source/date-limited, not jurisdiction-neutral. Fictional power tables are not facts about India or any real country. No ranking, merit score, endorsement or judgment of political actors/choices/policies; only correctness of educational factual assertions.

## Source and reference custody
All new fixtures are AUTHORED_DIAGNOSTIC / DEVELOPMENT, not golden or held-out. Public fixtures and expected values are intentionally visible for development, never a valid secret test set. Domain references are consultation links with original authored derivations, not copied textbooks or source-content rights grants. A hash pins bytes, not factual truth, independent approval or provenance authenticity. `metadata/section17/BATCH003_REFERENCE_CATALOG.json` retains actual source links and limitations.

## Executed selected tests
22 distinct selected methods passed in the 749-method cumulative run; method IDs are in this task's `TEST_RESULT.json` and `TEST_RESULT.txt`. They are a subset, not extra passes. Additional shared tests cover real CLI execution, candidate/reference hashes, SQLite persistence, retry controls, corruption, symlink preflight, concurrency, deterministic output, fixture regeneration and prior regressions. Final master verification additionally records independent extraction and execution of this atomic ZIP.

```bash
python -B tools/run_section17_tests.py --pattern test_civ_001.py --output-dir ../BIE-EVAL-CIV-001-new-tests
```
Use a new directory outside the immutable source. Keep prerequisite code, helpers and data in place. Source preimages and actual intermediate failure receipts are retained; do not run preimages as current code.

## Ownership and integration
Direct task dependencies: BIE-EVAL-REG-004, BIE-EVAL-BIO-001.
Owned implementation/test/fixture paths: `bie/evaluation/benchmarks/domains/civics.py`, `bie/evaluation/benchmarks/data/BIE-EVAL-CIV-001.json`, `tests/section17/test_civ_001.py`.
Shared wiring and batch tools are separately recorded in TASK_INTEGRATION_INDEX.json and BATCH003_CHANGE_LEDGER.json. Dependency runtime snapshots inside atomic ZIPs are support, not ten independent ownership claims. No blind overlay onto canonical main. Stop on a differing pre-existing owned path, review consumers and run canonical tests before adoption.

## Unclosed gates
No real-book/native BIE adapter, rendered video/frame/audio, game runtime, measured learner outcome, independently reviewed golden corpus or release authorization is supplied. Full-section audit/hardening/re-audit and original tasks31–50 remain open. Task028 in the separate app workflow remains paused (distinct from original Section17 task position28). No GitHub write or canonical continuation change occurred.
