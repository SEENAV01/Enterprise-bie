# Retry, Repair, Invalidation and Resume Policy

## Retry
A failed attempt remains immutable. Retry creates a new numbered attempt.

## Repair
Repair is modeled as a new attempt with remediation evidence. Repair cannot delete the original failure or lower a QA threshold.

## Invalidation
When an upstream artifact materially changes, downstream outputs derived from it must be invalidated according to lineage. Invalidated stages return to READY only after predecessor validity is restored.

## Resume
Persist run state after every transition. On restart:
- SUCCEEDED stages with valid artifact hashes may be reused.
- RUNNING stages from a dead worker are never assumed complete.
- Interrupted RUNNING stage becomes FAILED with recovery evidence, then may retry.
- PENDING stages become READY only when predecessors have valid SUCCEEDED outputs.

## Execution complete vs release
`EXECUTION_COMPLETE` means all configured execution stages succeeded. It does not mean the product is releasable. `ReleaseEvaluator` separately decides evidence-backed release status.
