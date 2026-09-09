# BIE v0.9 — End-to-End Orchestration Foundation

M1–M8 are now connected through a resumable, stateful pipeline contract.

```text
Book → M1 → M2 → M3 → M4 → M5 → M6 → M7
                                      ↘ M8
```

The included demo uses deterministic mock handlers to prove:
- ordered execution
- stage gates
- state persistence
- input/output hashing
- attempt counts
- failure stopping downstream stages
- a stable replacement point for real M1–M8 implementations

Run:
`pytest -q`

This is the integration foundation, not yet the production AI runtime. The next implementation should wire the actual PDF ingestion, model calls, retrieval/evidence verification, M6 planner, Scene DSL/Remotion renderer, and Game DSL runtime into these handlers.
