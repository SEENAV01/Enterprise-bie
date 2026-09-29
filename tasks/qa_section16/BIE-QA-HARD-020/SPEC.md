# BIE-QA-HARD-020 — Native compiler-to-final-audiovisual QA binding

Original audit-derived scope

Run the actual SceneIR-to-Remotion/production compiler path and bind compile, render, decoded media, timing and source content.

## Required closure evidence
- No injected renderer or generic FFmpeg fixture can stand in for the native build.
- Full versus smoke evidence and all required artifacts are distinguished.
- Short or missing audio/video, incorrect frame cadence and source drift block.

## Local implementation in H5
Hash-pinned canonical-checkout preflight and explicit invocation API for original compiler/full-render scripts, native receipt adaptation and mandatory fresh final-media re-decode with lineage byte inventory.

Code: bie/qa/media_runtime_v2/common.py, bie/qa/media_runtime_v2/native.py, bie/qa/media_runtime_v2/storage.py, bie/qa/media_runtime_v2/process.py

## Verification
Shared H5 suite: 162 unique tests, not 162 per task. Final executed receipts are under `hardening/section16_h5/evidence/final_source_suites`. The 24 targeted safeguard-removal probes and authored diagnostics are recorded separately, never added as extra unique unit tests.

## Unresolved closure requirements
- The full native compiler checkout and installed Remotion dependencies are not provisioned in this workspace; no native compile/render succeeded.
- Operational complete native evidence schemas, source-to-output provenance, production isolation and actual final audiovisual review remain open.

No historical obligation is closed by a local adapter, a synthetic authority, or an environment-blocked diagnostic. No Section15 or canonical GitHub code is changed.
