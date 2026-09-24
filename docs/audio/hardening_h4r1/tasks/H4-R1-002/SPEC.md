# BIE-AUDIO-H4-R1-002 — Fixed acoustic operation in the existing Linux worker

Verified parent: BIE-AUDIO-H3-005. Recovery mapping: documented BIE-AUDIO-H4-002.
This is newly implemented recovery code, not the unavailable original archive.
Inherited finding: AUDIO-AUDIT-001-F03; signed-acoustic authority also supports F02.

## Required behavior
Execute only the fixed measurement operation. Private namespaces, explicit read-only mounts, seccomp, resource limits, nonce and input/output hashes are checked. No key or durable store is mounted. No bounded-local fallback.

## Implementation and executable contract
Source: `kernel_runtime.py and kernel_entry.py` under `bie/audio/` unless an explicit path is given.
Shared contracts and limitations: `docs/audio/hardening_h4r1/CONTRACTS.md`.

```sh
python -B scripts/run_audio_tests.py --pattern test_audio_h4r_002.py --output /tmp/h4r-002.json
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
