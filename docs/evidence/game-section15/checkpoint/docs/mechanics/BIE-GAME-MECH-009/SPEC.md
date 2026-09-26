# BIE-GAME-MECH-009 — timeline reconstruction

## Scope
Enterprise-depth original implementation for Section 15 Batch 05. This capability is individually traceable inside the cumulative batch.

## Purpose
Implement **timeline reconstruction** as a semantic learning interaction, not a decorative UI gesture or slide transition.

## Architecture
- Implementation module: `bie/game_engine/mechanics_engine/timeline_reconstruction.py`
- Shared typed contracts: `mechanics_engine/contracts.py`
- Studio policy: `mechanics_engine/studio_policy.py`
- Deterministic receipts/replay: `mechanics_engine/common.py` + `replay.py`
- Governed dispatch: `mechanics_engine/pipeline.py`

## Required invariants
1. State change is causally tied to learner action.
2. Semantic motion communicates the state/concept change.
3. Accessibility labels and keyboard parity are explicit.
4. Source/reasoning/objective evidence is bound to the mechanic definition and receipt.
5. Identical governed input produces identical output/receipt.
6. Invalid/ambiguous inputs fail closed.
7. Reset is supported and replay is deterministic.
8. No premature answer reveal.
9. No speed-pressure requirement.
10. `product_accepted=false`.

## Verification
Task-specific positive execution, deterministic rerun, replay, runtime capability rejection, provenance rejection, adversarial invalid inputs, accessibility, studio-policy, and acceptance-boundary tests.

## Acceptance boundary
Passing this task is implementation evidence only. It does not imply Section 15 acceptance, learning-quality acceptance, real-book E2E acceptance, or product acceptance.
