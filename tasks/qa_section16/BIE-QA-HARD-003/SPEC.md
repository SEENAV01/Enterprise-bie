# BIE-QA-HARD-003 — Monotonic diagnostics across release consumers

Prevent any current readiness API or legacy adapter from discarding a reported blocking diagnostic.

Shared implementation and contracts: docs/qa_section16/hardening_h1/SPEC.md

Closure checks:
- PASS-labelled evidence with CONFIRMED_BROKEN_RENDER remains blocked in every supported consumer.
- Advisory versus blocking severity is explicit and typed; no blanket score or wrapper override.
- Legacy compatibility is documented; production callers cannot use the metadata-only SUCCESS path.
- Publication rejection and lower aggregator rejection agree on the same fixture.

No section exit or production acceptance.
