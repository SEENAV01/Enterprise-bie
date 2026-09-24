# BIE-AUDIO-H5-002 — Actual isolated local TTS, SYNC and dry MIX

Parent: BIE-AUDIO-H4-R1-005. Finding: AUDIO-AUDIT-001-F03.
These are justified engineering correction IDs, not newly invented original roadmap IDs.

## Requirement
Execute unchanged speech, timing, caption and dry MIX code in the canonical worker and verify every resulting byte and clock.

## Actual implementation
- `bie/audio/pipeline_worker.py`
- `bie/audio/pipeline_runtime.py`
- `bie/audio/pipeline_bundle.py`
- `scripts/audio_pipeline_worker.py`

## Executable verification
`python -B scripts/run_audio_tests.py --pattern test_audio_h5_002.py --output /tmp/h5-002.json`

Actual native waveform/proof; actual timeout and duration rejection; source/clock/caption/evidence tampering; nonregular/extra/missing files.

## Dependency and source compatibility
Uses the existing canonical dependency snapshots and AUDIO interfaces. All inherited Python files are unchanged. Atomic ZIPs contain the complete shared runnable runtime and fixtures rather than import-breaking isolated patches. The focused test suite is a repeated subset of the full AUDIO regression.

## Acceptance boundary
Implementation verified only to the actual recorded tests and benchmark. No section/product, cinematic speech, independent pronunciation, deployed trust, full-enterprise, real-book or real-render acceptance. See ../../CONTRACTS.md and ../../REAUDIT.md.

## Rollback
Use the exact parent H4 Recovery R1 archive in the master backup. Preserve this task's evidence; do not overwrite newer GitHub/Codex work with either snapshot.
