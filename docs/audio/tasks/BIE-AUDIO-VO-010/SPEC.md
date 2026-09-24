# BIE-AUDIO-VO-010 — Verified TTS cache

Original registry task. Implementation contracts, bounded supported behavior, required inputs, errors and acceptance boundaries are in `docs/audio/BATCH002_CONTRACTS.md`.

Declared task suite: 20 tests in tests/audio/test_audio_vo_010.py. For VO-009, this includes twelve actual installed-eSpeak tests, not just provider doubles. Atomic archives include the first two batches' source dependency closure but only the selected task suite and shared support. They are independently runnable; not ordered deltas. Missing eSpeak for real tests is an explicit deployment failure.

No neural-voice, pronunciation, timing-alignment, cinematic, real-book or whole-product acceptance is awarded by passing this task suite. Current section remains in progress. Canonical GitHub integration is deferred until full section exit.
