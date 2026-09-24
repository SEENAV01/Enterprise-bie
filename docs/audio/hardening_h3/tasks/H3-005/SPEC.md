# BIE-AUDIO-H3-005 — End-to-end durable CLI and restart/tampering evidence

Finding: AUDIO-AUDIT-001-F03. Engineering subdivision, not a new original roadmap ID.

Implementation: `scripts/audio_durable.py`, `scripts/benchmark_audio_durable.py`.

Full input/output/error/authority boundaries are in docs/audio/hardening_h3/CONTRACTS.md.
Runnable task suite:

```sh
python -B scripts/run_audio_tests.py --pattern test_audio_h3_005.py --output /tmp/h3-005.json
```

Current task tests: 12. The atomic ZIP includes required shared-source/test/dependency closure and is independently runnable; it is not a sequential delta or full-monorepo copy. Native legacy acoustic tests require the documented native dependencies. No production credentials or model binaries are bundled.

A passing test suite does not assert phonetic, multilingual, cinematic, kernel-isolation, real-book or product acceptance. F01/F02, wider F03 and F04 remain open.
