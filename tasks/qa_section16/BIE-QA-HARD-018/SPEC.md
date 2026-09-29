# BIE-QA-HARD-018 — Continuous animation, nonlinear state and safety coverage

Original audit-derived scope

Connect full native timelines/simulation state to trajectory, semantic-invariant, reduced-motion and flash/accessibility checks.

## Required closure evidence
- An intersample defect cannot escape endpoint-only checks.
- Springs, camera/composition and complex motion are checked or rejected as unsupported.
- Reduced motion preserves teaching meaning; comfort thresholds are not clinical certification.

## Local implementation in H5
Exact cubic scalar enclosures, full discrete state/meaning/clock coverage, native Event temporal QA, reduced-motion limits and every-frame luminance/motion screening.

Code: bie/qa/media_runtime_v2/common.py, bie/qa/media_runtime_v2/motion.py, bie/qa/media_runtime_v2/storage.py, bie/qa/media_runtime_v2/process.py

## Verification
Shared H5 suite: 162 unique tests, not 162 per task. Final executed receipts are under `hardening/section16_h5/evidence/final_source_suites`. The 24 targeted safeguard-removal probes and authored diagnostics are recorded separately, never added as extra unique unit tests.

## Unresolved closure requirements
- Native timeline/renderer attestation and arbitrary spring/3-D/camera composition remain open.
- Full output flash/accessibility coverage and calibrated comfort thresholds remain open; screening is not certification.

No historical obligation is closed by a local adapter, a synthetic authority, or an environment-blocked diagnostic. No Section15 or canonical GitHub code is changed.
