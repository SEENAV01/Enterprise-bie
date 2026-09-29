# BIE-QA-HARD-010 — Calibrated quality floors and evaluator agreement interface

## Original audit requirement
Define measured rubric floors and rater disagreement/calibration contracts for academic, teaching and cinematic quality; consume EVAL-held data, do not fabricate scores.

## Implemented local scope
Consumes actual corpus and prediction JSON bytes with operator-owned criterion floors, rater versions, principals, groups, domain and language. Recomputes per-criterion held-out accuracy/agreement and critical false-clear counts. Duplicate/cross-split source or input identities and incomplete case/rater coverage are rejected. A strong style score cannot compensate for failed academic criteria.

## Executed / tested behavior
- Blind-ID and holdout provenance structure, corrupted calibration bytes, stale profiles, class coverage and rater drift are tested.
- Independent/scoped synthetic approval demonstrates the positive contract; diagnostic corpus results never establish empirical calibration.

## Required closure still open
- No genuine independent EVAL-held rater dataset, human review or learner study was supplied.
- Empirical thresholds, external label quality and actual blinded collection remain OPEN.
- The API is a measurement/interface implementation, not fabricated cinematic scores or learning-efficacy certification.

This task has a local adapter/interface implementation, not full operational closure. Source files and old evaluations are never rewritten to create a pass. No release is authorized. Read the shared execution receipts; do not multiply shared test counts by five.
