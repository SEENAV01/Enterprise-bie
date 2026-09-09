# BIE-INFRA-E2E-RUNTIME-001

## Goal
Reference end-to-end enterprise runtime wiring:

Orchestrator -> durable queue -> queue worker consumer -> worker runtime ->
fenced commit -> artifact catalog/state persistence -> queue ACK.

## Invariants
- enqueue never marks a stage successful
- ACK is impossible before durable commit returns successfully
- commit failure produces retry and no ACK
- queue delivery count and stage attempt stay distinct
- artifact refs and evidence refs must be non-empty on success
- run/release SUCCESS is outside this layer
- repeated delivery may occur; duplicate-safe commit is required
