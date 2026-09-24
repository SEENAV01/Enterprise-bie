# BIE-AUDIO-MIX-004 — silence trim

Original Section 14 task, no newly invented numbering. Continuation of the supplied Batch 004 recovery source.

Implementation: `bie/audio/silence_trim.py, mix_clock.py, mix_pipeline.py`. Exact supported behavior, source inputs, limits, error conditions and exclusions: `docs/audio/BATCH004_CONTRACTS.md`, MIX-004 section.

Atomic test suite: `tests/audio/test_audio_mix_004.py`. Combined boundaries: `test_audio_batch004_integration.py`, `test_audio_mix_io.py`; native benchmark: `scripts/benchmark_audio_batch004.py`.

Input bytes and source references must remain traceable; no silent clipping, truncation or resampling. Process failures/unreachable policy targets must reject or explicitly require review. A passing task suite does not imply whole AUDIO, real-book, acoustic, Remotion or product acceptance.

Atomic package: standalone shared source closure with this task's declared test suite; not an ordered delta, not a full monorepo. Native dependencies remain external. GitHub integration only at section exit.
