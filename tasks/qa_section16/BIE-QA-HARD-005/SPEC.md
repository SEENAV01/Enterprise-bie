# BIE-QA-HARD-005 — Canonical local task and integration metadata index

Normalize all76 task-to-code/spec/test references, all22 namespaces, and integration-plan state without deleting historical records.

## Closure requirements
- A single schema indexes task evidence regardless of its historic directory.
- Performance/publication namespaces cannot disappear from integration inventory.
- No stale latest-task/status fields; test identity includes suite/source-path provenance.
- Byte-compare protected originals and archive superseded metadata.

Current local checks are implemented and verified; final closure awaits section re-audit and canonical integration.
Shared specification: `docs/qa_section16/hardening_h2/SPEC.md`.
