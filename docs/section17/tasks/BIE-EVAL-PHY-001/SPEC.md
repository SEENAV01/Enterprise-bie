# BIE-EVAL-PHY-001 — Coulomb benchmark

## Scope and position
Original registry Section17, pages19–20; original sequence 5. This is an additive scoped implementation, not a replacement for existing BIE engines. Local status: **SCOPED_LOCAL_IMPLEMENTATION_VERIFIED**. Original capability closure and enterprise acceptance remain pending.

## Observable behavior
Signed 3D point-charge force, vector superposition, inverse-square distance, explicit SI conversions, configurable pinned Coulomb constant and coincidence rejection.

## Inputs, outputs and invariants
Authoring inputs use strict typed records/JSON with case identity, exact source references, explicit derivation, split and leakage group. Expected values are kept separate from candidate-facing prompts. Snapshot/candidate/config/output identities are hashed. Data is never evaluated as Python or a shell command. Failure states are explicit; no missing or invalid evidence is upgraded to acceptance.

The implementation files are the executable interface specification. Public APIs validate all declared fields; source files contain supported operations and output keys. Scientific results use explicit units and manually authored expected answers. Unsupported profiles return a typed rejection; this does not count as implementation of those profiles.

## Dependencies and owned paths
Direct atomic dependencies: BIE-EVAL-REG-004.

- `bie/evaluation/benchmarks/domains/coulomb.py`
- `bie/evaluation/benchmarks/data/BIE-EVAL-PHY-001.json`
- `tests/section17/test_phy_001.py`

## Tests and seeded defects
Run `python -B -m unittest discover -s tests/section17 -p 'test_phy_001.py' -v` from the assembled dependency closure. This task suite has 20 distinct test methods. Exact IDs and executed results are in its TEST_RESULT files. The full cumulative suite additionally exercises cross-task persistence, policy binding, malformed inputs, CLI import/export, corrupted data and package safety. A test method's subcases are not added as extra test methods.

## Scope boundary and acceptance requirements
Electrostatic point charges in vacuum only. Not dielectric interfaces, distributed fields, relativity, visual explanations or native BIE physics acceptance. Ten authored development cases; no independently reviewed hidden Coulomb corpus.

Review `metadata/section17/GAP_LEDGER.json`. Section16 integration, exact canonical candidate regression, actual native BIE artifacts, independent source/benchmark assessment, remaining EVAL metrics/raters/floors and final real-book proof are not replaced by these local results. A benchmark runner or passing authored fixture is not evidence of cinematic quality, scientific pedagogy or learning improvement.

## Preservation and packaging
The existing `bie/evaluation/contracts.py` and both parent initializers are not included as replacements. Atomic ZIPs carry owned payload plus direct dependency metadata; their dependencies are supplied in the same batch. The cumulative payload is ready to extract in a new scratch directory, not over GitHub main. No commit, PR, merge, global continuation update or Task028 resumption is performed.
