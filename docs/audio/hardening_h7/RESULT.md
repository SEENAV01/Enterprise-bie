# BIE AUDIO Hardening H7

Implemented the next bounded F03 slice over the exact H6 parent: durable segment-level cache identity/lifecycle plus deterministic long-book batching, resume and selective invalidation decisions.

Fresh focused execution: **49/49 H7 tests PASS**. Parent H6 stem tests were rerun together with H7 for **57/57 PASS**. No complete AUDIO-wide regression was claimed in this batch.

## Atomic tasks
- BIE-AUDIO-H7-001 — content/configuration-bound segment cache identity and media-bound receipt.
- BIE-AUDIO-H7-002 — canonical CAS + SQLite idempotency + fenced lease durable cache with restart/recovery checks.
- BIE-AUDIO-H7-003 — bounded orphan inspection/pruning and selective identity invalidation semantics.
- BIE-AUDIO-H7-004 — deterministic long-book batching/resume with no truncation or reorder.
- BIE-AUDIO-H7-005 — preservation, regression evidence, continuation and explicit acceptance limits.

## Important limits
Paid/neural external-call uncertainty, production secret/key custody, F02 multilingual/calibrated evaluator authority, F04 canonical DIR/ANI/COMP invalidation/handoff, actual pinned render, independent listening and real-book acceptance remain open. H7 is hardening progress, not section exit.
