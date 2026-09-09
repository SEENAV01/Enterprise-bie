# BIE v0.9 Architecture

## Goal
Turn M1–M8 from independent prototypes into one resumable job pipeline.

## State
Each job records:
- stage status
- attempts
- input/output hashes
- timestamps
- error
- metadata
- artifact references

## Gate semantics
A stage runs only when the previous stage is PASS or REVIEW.
FAILED stages stop downstream execution.

## Production replacement
`mock_pipeline.py` is deliberately deterministic. Replace handlers with the actual M1–M8 modules and keep the orchestration/state contract unchanged.

## Incremental recomputation
A production artifact store should key artifacts by `(job_id, stage, input_hash, component_version)`. If the same input and component version already exist, the stage can be reused rather than recomputed.

## Human review
M5 REVIEW should pause downstream generation or route only affected claims/units into repair, depending on policy.

## Large books
For 500+ page books, the next production layer should shard work by page/chunk, then merge deterministically at M3/M4. Job state should track shard-level status and hashes.

## Outputs
M8 is the terminal planning layer. M7 feeds a real Remotion renderer; M8 feeds a real game runtime.
