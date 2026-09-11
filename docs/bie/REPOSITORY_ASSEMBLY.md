> Historical snapshot: this document records the earlier 766-archive / 376-batch assembly. It is preserved as history, not the current canonical state. Read `CURRENT_STATE.md` and `../../task_registry/continuation.json` for the 796-archive canonical state and RE-TEMP-003 checkpoint.

# Repository Assembly 001

## Scope and evidence

Recovered 766 BIE ZIPs, including duplicated downloads and historical variants. The original archive bundle contains every ZIP byte-for-byte. `manifests/archive_inventory.json` records archive hashes and `manifests/file_inventory.json` records all 12,259 original file members and their expanded locations. Derived caches remain inside originals. `scripts/verify_assembly.py` checks the archive bundle and all expanded imported files.

The 376 enterprise packages contribute 390 distinct source paths under `app/bie`. Original contents remain in `batches`; all earlier packages remain in `historical`. This source consolidation does not establish complete end-to-end wiring of every historical M-series implementation into the new enterprise flow.

## Source collisions resolved

| Working source | Retained richer source | Reduced later copy preserved in |
| --- | --- | --- |
| `enterprise/worker_scheduler.py` | BIE_INFRA_WORKER_001 | BIE_INFRA_EXECUTOR_001 |
| `enterprise/leases.py` | BIE_INFRA_RECOVERY_001 | BIE_INFRA_EXECUTOR_001 |
| `enterprise/run_state.py` | BIE_INFRA_STATE_001 | BIE_INFRA_ORCH_001 |

The richer scheduler retains capability/GPU/affinity validation, reservation capacity and health behavior. The richer lease manager retains scope checks, expiry/recovery evidence and fencing. The richer state machine retains validated transitions, timestamps, invalidation and interruption recovery.

## Working changes required by the merge

1. `run_state.retry` previously rewrote the failed attempt's state to READY before adding another attempt. Removed that mutation so failure state, timestamps and evidence remain intact. A new regression test checks the entire old attempt. The imported working test now expects FAILED; the erroneous original expectation remains untouched in `batches` and the original ZIP.
2. The executor batch used a reduced positional scheduler dataclass. Its working tests now pass `max_concurrency` and `slot_cost` by keyword to preserve their intended meaning with the richer original dataclasses.
3. The concept merge/split original test indexed the integer returned by `len`, causing a TypeError. Corrected only its working copy to take the length of `subconcepts`. No production behavior or assertion was removed.
4. A common test runner loads tests with unique names and routes all imports to the combined source tree. Historical source trees are not added to that import path.

The original files in `batches` and `historical` are immutable provenance snapshots; working tests are in `tests/imported`.

## Remaining acceptance work

- Reconcile the lightweight reasoning decision factory with the richer reasoning contract and canonical lineage envelope.
- Connect source/knowledge/prerequisite/reasoning outputs through the active enterprise pipeline and characterize the retained legacy pipeline before any migration.
- Validate against real books and a multi-domain golden set, then downstream pedagogy, video compiler, actual render and revision game runtime.
- Implement the governed cumulative-learning requirement with evaluation evidence; it is currently a preserved product requirement.

Imported component tests passing is evidence of unit compatibility. It does not prove real OCR, production queues, distributed persistence, live model behavior, complete media production or enterprise acceptance.
