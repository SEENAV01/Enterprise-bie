# BIE-AUDIO-H5-005 — Technical CLI, interoperable export and cold restart

Parent: BIE-AUDIO-H4-R1-005. Finding: AUDIO-AUDIT-001-F03.
These are justified engineering correction IDs, not newly invented original roadmap IDs.

## Requirement
Provide explicit technical/review CLI and exclusive exact-source export; demonstrate actual process restart and original MIX-reader interoperability.

## Actual implementation
- `bie/audio/pipeline_io.py`
- `scripts/audio_pipeline.py`
- `scripts/benchmark_audio_h5.py`
- `scripts/run_audio_module_set.py`

## Executable verification
`python -B scripts/run_audio_tests.py --pattern test_audio_h5_005.py --output /tmp/h5-005.json`

Independent expected identity, manifest/signature tampering, export overwrite/file hygiene, private key file policy, real cold CLI two-scene benchmark.

## Dependency and source compatibility
Uses the existing canonical dependency snapshots and AUDIO interfaces. All inherited Python files are unchanged. Atomic ZIPs contain the complete shared runnable runtime and fixtures rather than import-breaking isolated patches. The focused test suite is a repeated subset of the full AUDIO regression.

## Acceptance boundary
Implementation verified only to the actual recorded tests and benchmark. No section/product, cinematic speech, independent pronunciation, deployed trust, full-enterprise, real-book or real-render acceptance. See ../../CONTRACTS.md and ../../REAUDIT.md.

## Rollback
Use the exact parent H4 Recovery R1 archive in the master backup. Preserve this task's evidence; do not overwrite newer GitHub/Codex work with either snapshot.
