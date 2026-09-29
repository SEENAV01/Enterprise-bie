# BIE-QA-HARD-022 — Native-origin game QA adapter

Original audit-derived scope

Consume externally completed Section15 outputs through their real entrypoint/module load path. Do not rebuild or modify Section15 here.

## Required closure evidence
- HTTP/native origin, assets and interactions execute in an approved environment.
- about:blank/injected mode never becomes native acceptance.
- Environment policy blocks are retained; no policy bypass to turn the gate green.

## Local implementation in H5
Current native DeploymentEvidence consumption explicitly requires real browser-origin navigation; exact package/module/load hashes, timestamps, screenshots and UI errors are checked. HTTP-only capture has no injected fallback.

Code: bie/qa/media_runtime_v2/common.py, bie/qa/media_runtime_v2/game.py

## Verification
Shared H5 suite: 162 unique tests, not 162 per task. Final executed receipts are under `hardening/section16_h5/evidence/final_source_suites`. The 24 targeted safeguard-removal probes and authored diagnostics are recorded separately, never added as extra unique unit tests.

## Unresolved closure requirements
- The supplied diagnostic UI is not Section15 native output. Native-origin Section15 execution and trusted capture attestation remain open.
- Managed browser policy is never altered or bypassed; any blocked HTTP attempt is retained as a blocker.

No historical obligation is closed by a local adapter, a synthetic authority, or an environment-blocked diagnostic. No Section15 or canonical GitHub code is changed.
