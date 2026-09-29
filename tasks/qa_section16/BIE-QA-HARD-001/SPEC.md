# BIE-QA-HARD-001 — Typed terminal-report adapters and complete blocker propagation

Replace top-level PASS recognition with closed-world registered report/ledger adapters. Preserve nested failures and every recognized obligation collection.

Shared implementation and contracts: docs/qa_section16/hardening_h1/SPEC.md

Closure checks:
- Unknown schema and unregistered version are rejected; no status-only fallback.
- Nested FAIL/ERROR/SKIPPED/review-required checks block despite outer PASS.
- Open obligations in gaps and all batch-specific lists block; closed fixture permits evaluation.
- Reproduce and then reject PUB-UNKNOWN-SCHEMA, PUB-NESTED-FAIL and PUB-OBLIGATION-SUBLIST.

No section exit or production acceptance.
