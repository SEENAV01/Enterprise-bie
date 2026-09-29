# BIE-QA-HARD-002 — Transitive evidence identity, scope and time binding

Require adapter-verified terminal bindings through candidate, run, revision, evaluator policy, gate, inspected bytes and capture/creation times.

Shared implementation and contracts: docs/qa_section16/hardening_h1/SPEC.md

Closure checks:
- Foreign candidate/run/revision/gate is rejected before authorization.
- Future/expired terminal evidence cannot borrow a fresh wrapper lifetime.
- Permit explicitly typed timeless facts only through a separate justified schema, never arbitrary omission.
- Reproduce then reject PUB-FOREIGN-BINDING and PUB-FUTURE-TERMINAL.

No section exit or production acceptance.
