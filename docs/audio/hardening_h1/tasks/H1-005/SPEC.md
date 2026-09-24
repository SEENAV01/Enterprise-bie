# BIE-AUDIO-H1-005 — Live-gated CLI, provenance and conformance checks

Authority: engineering subdivision of existing AUDIO-AUDIT-001-F01. This is not an original-roadmap task or recovered historical hardening number.

Source: scripts/audio_neural.py, scripts/benchmark_audio_h1.py. Complete cross-task contract and limits: `docs/audio/hardening_h1/CONTRACTS.md`.

Test suite: `tests/audio/test_audio_h1_005.py`, 15 declared tests. Use `python -B scripts/run_audio_tests.py --pattern test_audio_h1_005.py --output /tmp/audio-h1-005.json` from the extracted package. Tests use explicit offline provider fixtures; subprocess transport and native audio processing are actual local execution.

Acceptance: passing tests does not establish live neural speech, phonetic correctness, cinematic voice quality, kernel sandbox deployment, real-book or render acceptance. Missing credentials must block remote execution. No automatic paid calls or GitHub writes.
