# BIE-AUDIO-H3-001 — Exact canonical durable dependency and request identity

Finding: AUDIO-AUDIT-001-F03. Engineering subdivision, not a new original roadmap ID.

Implementation: `bie/audio/durable_contract.py`, `CANONICAL_AUDIO_DEPENDENCIES.json`.

Full input/output/error/authority boundaries are in docs/audio/hardening_h3/CONTRACTS.md.
Runnable task suite:

```sh
python -B scripts/run_audio_tests.py --pattern test_audio_h3_001.py --output /tmp/h3-001.json
```

Current task tests: 17. The atomic ZIP includes required shared-source/test/dependency closure and is independently runnable; it is not a sequential delta or full-monorepo copy. Native legacy acoustic tests require the documented native dependencies. No production credentials or model binaries are bundled.

A passing test suite does not assert phonetic, multilingual, cinematic, kernel-isolation, real-book or product acceptance. F01/F02, wider F03 and F04 remain open.
