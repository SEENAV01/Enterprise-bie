# BIE-AUDIO-H4-R1-001 — Canonical worker profile and exact dependency identities

Verified parent: BIE-AUDIO-H3-005. Recovery mapping: documented BIE-AUDIO-H4-001.
This is newly implemented recovery code, not the unavailable original archive.
Inherited finding: AUDIO-AUDIT-001-F03; signed-acoustic authority also supports F02.

## Required behavior
Approve a bounded Linux/no-proc profile only after exact canonical source, acoustic engine, selected runtime and adapter identities match. Profile discovery is not approval.

## Implementation and executable contract
Source: `kernel_profile.py` under `bie/audio/` unless an explicit path is given.
Shared contracts and limitations: `docs/audio/hardening_h4r1/CONTRACTS.md`.

```sh
python -B scripts/run_audio_tests.py --pattern test_audio_h4r_001.py --output /tmp/h4r-001.json
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
