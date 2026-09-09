# BIE continuation rules

Read `BIE_CONTEXT_HANDOFF.md` and `docs/bie/CURRENT_STATE.md` before continuing.

- Preserve original snapshots in `batches/`, `historical/` and the archive backup. Modify working source in `app/bie/` and working tests in `tests/`.
- Retain task IDs, specifications, evidence, provenance and acceptance boundaries. Never promote historical status claims without required evidence.
- Source-derived prerequisite generation cannot require a learner questionnaire or knowledge self-report.
- Preserve the first-class video and interactive revision game architecture and the governed cumulative-learning requirement.
- For each completed batch, run meaningful verification, commit the intended changes to the verified repository, update the checkpoint and provide a downloadable ZIP backup with its exact commit SHA. Report any blocked upload honestly.
- Avoid silently replacing richer historical implementations with reduced helper copies. Document compatibility and migration decisions.
- `python3 scripts/verify_assembly.py` verifies imported source preservation. `python3 scripts/test_enterprise.py` runs combined enterprise tests. Neither command is a production acceptance gate by itself.
