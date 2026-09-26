# BIE continuation rules

Read `BIE_CONTEXT_HANDOFF.md`, `docs/bie/CURRENT_STATE.md` and `task_registry/continuation.json` before continuing.

- This is the existing enterprise BIE project. Preserve its architecture, task IDs, implementation history and acceptance boundaries.
- Working source is `bie/`; applications belong in `apps/`. `app/bie` is compatibility code only. Do not add production source to ZIP snapshots.
- `batches/`, `historical/`, original backups, and `docs/evidence/assembly-001/` are immutable evidence. Every original file has one disposition in `manifests/lossless_migration.csv`.
- New tasks follow dependency check, implementation, unit/contract tests, evidence, canonical integration, regression, registry update, GitHub synchronization and a downloadable ZIP backup. Do not redo completed Prerequisite or Math tasks.
- Preserve video AND playable revision games, structured IR, source-derived prerequisites and governed cumulative learning. No raw Book → LLM → Remotion shortcut.
- Preserve richer historical implementations. Differing hashes need documented conflict selection; missing code is never reconstructed from filenames.
- Run `python scripts/integrated_check.py`. It verifies preservation and all working enterprise tests, not product acceptance.
- IMPLEMENTED is not ACCEPTED. Real-book integration and downstream compile/render/game QA evidence remain required.
- Verify actual GitHub write and exact remote commit/tree readback before reporting synchronization. Never force-push or overwrite concurrent changes.
- Provide exact commit SHA(s) and a full repository backup. The user must not manually assemble atomic ZIPs.

Previous Reasoning integration authority is `docs/evidence/reasoning-integration-001/USER_INTEGRATION_PROMPT.txt`. The Reasoning implementation scope is complete and not accepted. Preserve the 56 Temporal and 21 QA/hardening tasks and distinguish original-roadmap work from hardening. Do not invent another RE task without a concrete integration/E2E gap. Follow `task_registry/continuation.json` and preserve the real-textbook, downstream-consumer, benchmark and product acceptance blockers.


Current PED integration authority is `docs/evidence/pedagogy-integration-002/USER_INTEGRATION_PROMPT.txt`. PED is implementation-scope complete and not accepted. Preserve all 58 original PED archives and their task/evidence provenance; source is `bie/pedagogy/`. Run the integrated gate, which includes PED tests and supplemental ingestion integrity. Retain the real multi-domain textbook, DIR, empirical/benchmark and final lesson/video/game acceptance blockers.

Current Director integration authority is `docs/evidence/director-integration-003/USER_INTEGRATION_PROMPT.txt`. DIR is implementation-scope complete and not accepted. Preserve its 37 original tasks, 22 audit-derived hardening tasks, 59 immutable archives and 610 member records; source is `bie/director/`. The enterprise gate includes all 683 DIR tests. Continue with the approved downstream VIS/ANI/Game roadmap or concrete real-source/product acceptance evidence; never infer rendered-media or playable-game acceptance from DIR contract tests.
