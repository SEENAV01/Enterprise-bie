# BIE-QA-HARD-021 — Acoustic alignment, pronunciation and rendered captions

Original audit-derived scope

Consume genuine speech/alignment/listening evidence and final muxed captions; cover approved languages, terminology and audio profiles.

## Required closure evidence
- Engine timestamps alone do not prove phonetic boundaries.
- Wrong pronunciation, missing words, delayed captions and clipping have independent controls.
- Actual rendered credits/captions remain legible; translations preserve meaning.

## Local implementation in H5
Actual PCM and caption bytes, independent listening/alignment record authentication, per-occurrence word coverage/forms, exact sample clocks and bounded reference-waveform offset estimation.

Code: bie/qa/media_runtime_v2/common.py, bie/qa/media_runtime_v2/speech.py

## Verification
Shared H5 suite: 162 unique tests, not 162 per task. Final executed receipts are under `hardening/section16_h5/evidence/final_source_suites`. The 24 targeted safeguard-removal probes and authored diagnostics are recorded separately, never added as extra unique unit tests.

## Unresolved closure requirements
- No independent human listening/forced aligner or real phonetic word-boundary measurement was executed.
- Rendered caption visibility, final native mux/playback, translation validity and live acoustic assessment remain open.

No historical obligation is closed by a local adapter, a synthetic authority, or an environment-blocked diagnostic. No Section15 or canonical GitHub code is changed.
