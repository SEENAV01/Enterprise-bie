# BIE-AUDIO-H5-003 — Executor authority bound to source and outputs

Parent: BIE-AUDIO-H4-R1-005. Finding: AUDIO-AUDIT-001-F03.
These are justified engineering correction IDs, not newly invented original roadmap IDs.

## Requirement
Sign only actual validated native execution with an external approved host-side executor key; reject obsolete or forged evidence on every reuse.

## Actual implementation
- `bie/audio/pipeline_evidence.py`

## Executable verification
`python -B scripts/run_audio_tests.py --pattern test_audio_h5_003.py --output /tmp/h5-003.json`

Real signature plus wrong domains/keys/roles, revoked/expired/unapproved trust, source/job/revision substitution, escalation and fractional clock boundaries.

## Dependency and source compatibility
Uses the existing canonical dependency snapshots and AUDIO interfaces. All inherited Python files are unchanged. Atomic ZIPs contain the complete shared runnable runtime and fixtures rather than import-breaking isolated patches. The focused test suite is a repeated subset of the full AUDIO regression.

## Acceptance boundary
Implementation verified only to the actual recorded tests and benchmark. No section/product, cinematic speech, independent pronunciation, deployed trust, full-enterprise, real-book or real-render acceptance. See ../../CONTRACTS.md and ../../REAUDIT.md.

## Rollback
Use the exact parent H4 Recovery R1 archive in the master backup. Preserve this task's evidence; do not overwrite newer GitHub/Codex work with either snapshot.
