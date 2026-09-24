# BIE-AUDIO-H5-004 — Canonical durable pipeline lifecycle and reuse

Parent: BIE-AUDIO-H4-R1-005. Finding: AUDIO-AUDIT-001-F03.
These are justified engineering correction IDs, not newly invented original roadmap IDs.

## Requirement
Use existing CAS/catalog/artifact/lease/claim APIs for verified whole-run persistence, concurrency, heartbeat, bounded recovery and reuse.

## Actual implementation
- `bie/audio/pipeline_durable.py`

## Executable verification
`python -B scripts/run_audio_tests.py --pattern test_audio_h5_004.py --output /tmp/h5-004.json`

Real CAS reopen/corruption, provenance chain, current-trust cache reuse, conflicting inputs, concurrent owners, stale epochs, injected claim/lease crash and attempt limits.

## Dependency and source compatibility
Uses the existing canonical dependency snapshots and AUDIO interfaces. All inherited Python files are unchanged. Atomic ZIPs contain the complete shared runnable runtime and fixtures rather than import-breaking isolated patches. The focused test suite is a repeated subset of the full AUDIO regression.

## Acceptance boundary
Implementation verified only to the actual recorded tests and benchmark. No section/product, cinematic speech, independent pronunciation, deployed trust, full-enterprise, real-book or real-render acceptance. See ../../CONTRACTS.md and ../../REAUDIT.md.

## Rollback
Use the exact parent H4 Recovery R1 archive in the master backup. Preserve this task's evidence; do not overwrite newer GitHub/Codex work with either snapshot.
