# BIE-AUDIO-H4-R1-003 — Signed v2 execution and exact request provenance

Verified parent: BIE-AUDIO-H3-005. Recovery mapping: documented BIE-AUDIO-H4-003.
This is newly implemented recovery code, not the unavailable original archive.
Inherited finding: AUDIO-AUDIT-001-F03; signed-acoustic authority also supports F02.

## Required behavior
Require independent issuer and profile approval. Sign media, job, selected profile, native execution and optional exact durable-request fingerprint; reject legacy-only, replayed, revoked, expired or relabelled evidence.

## Implementation and executable contract
Source: `kernel_evidence.py` under `bie/audio/` unless an explicit path is given.
Shared contracts and limitations: `docs/audio/hardening_h4r1/CONTRACTS.md`.

```sh
python -B scripts/run_audio_tests.py --pattern test_audio_h4r_003.py --output /tmp/h4r-003.json
```

The task archive contains the complete required shared-source/test/dependency closure
and all recovery specs so it is runnable independently, not a sequential patch.
Its task receipt identifies exactly which suite was run on fresh extracted bytes.
Additional source in that closure does not claim additional tasks were independently
accepted. No model, font, native binary, signing key or production credentials ship.

## Verification and exit
Positive, negative, tamper, authority and relevant native cases must actually pass;
no skipped native test counts as a pass. See TASK_RESULT.json and TEST_RESULT.txt.
A passing task suite does not close F01, F02, full F03, F04 or enterprise acceptance.
