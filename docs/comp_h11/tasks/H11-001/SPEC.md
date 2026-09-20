# BIE-COMP-H11-001 — Verified visual asset handoff

Bind existing asset-bundle receipts, verify actual bounded image/video bytes and retain source/rights assertions.

Full contract and boundaries: `docs/comp_h11/CONTRACTS.md`. This is an audit-derived implementation task from original asset/media handoff and existing R01/R02, not an invented original-roadmap ID.

Inputs/outputs: existing Scene IR and ASSET bundle contracts; a source-bound visual manifest, generated component/source evidence, and verified bytes on adopted publication paths. Tasks are cross-dependent: restore all four H11 deltas onto exact H10 before testing. Intermediate deltas are source assembly, not runnable releases.

Tests: `PYTHONPATH=app:. PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.compiler.test_comp_h11_001 -v` (38 tests). Actual pre-package execution is in TEST_RESULT.txt; final extracted release execution is bound externally to the integrated archive SHA256.

Success means the bounded implementation and negative tests pass. No full pinned-project compile, actual Remotion render, spoken-audio/transcript verification, license approval, real-book success or product acceptance is implied.
