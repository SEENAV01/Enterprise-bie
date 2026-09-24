# BIE-AUDIO-H4-R1-004 — Canonical H3 durable reuse with kernel-required evidence

Verified parent: BIE-AUDIO-H3-005. Recovery mapping: documented BIE-AUDIO-H4-004.
This is newly implemented recovery code, not the unavailable original archive.
Inherited finding: AUDIO-AUDIT-001-F03; signed-acoustic authority also supports F02.

## Required behavior
Extend the unchanged H3 three-envelope chain with a fourth signed-kernel envelope. Reuse canonical CAS/catalog/lease/claim APIs. Reverify current authority and source before cache use and both fenced completion markers.

## Implementation and executable contract
Source: `kernel_durable.py` under `bie/audio/` unless an explicit path is given.
Shared contracts and limitations: `docs/audio/hardening_h4r1/CONTRACTS.md`.

```sh
python -B scripts/run_audio_tests.py --pattern test_audio_h4r_004.py --output /tmp/h4r-004.json
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
