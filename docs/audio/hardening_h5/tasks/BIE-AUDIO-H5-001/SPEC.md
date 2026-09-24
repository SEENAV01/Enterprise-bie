# BIE-AUDIO-H5-001 — Source-bound request and approved execution profile

Parent: BIE-AUDIO-H4-R1-005. Finding: AUDIO-AUDIT-001-F03.
These are justified engineering correction IDs, not newly invented original roadmap IDs.

## Requirement
Reconstruct exact declared narration, enforce finite budgets and discover the real fixed namespace runtime without treating discovery as trust approval.

## Actual implementation
- `bie/audio/pipeline_contract.py`
- `bie/audio/pipeline_profile.py`
- `bie/audio/pipeline_discovery.py`
- `scripts/audio_pipeline_discover.py`

## Executable verification
`python -B scripts/run_audio_tests.py --pattern test_audio_h5_001.py --output /tmp/h5-001.json`

Source/reference/plan tampering; budget/type/UUID/command validation; exact profile drift and launcher checks.

## Dependency and source compatibility
Uses the existing canonical dependency snapshots and AUDIO interfaces. All inherited Python files are unchanged. Atomic ZIPs contain the complete shared runnable runtime and fixtures rather than import-breaking isolated patches. The focused test suite is a repeated subset of the full AUDIO regression.

## Acceptance boundary
Implementation verified only to the actual recorded tests and benchmark. No section/product, cinematic speech, independent pronunciation, deployed trust, full-enterprise, real-book or real-render acceptance. See ../../CONTRACTS.md and ../../REAUDIT.md.

## Rollback
Use the exact parent H4 Recovery R1 archive in the master backup. Preserve this task's evidence; do not overwrite newer GitHub/Codex work with either snapshot.
