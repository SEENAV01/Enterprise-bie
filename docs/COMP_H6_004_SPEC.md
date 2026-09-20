# BIE-COMP-H6-004 — Scheduled narration and synchronized captions

Source finding: existing H3-R02 state/event/audio-consumer backlog. This task is part of the existing audit correction cycle, not a new full section audit.

Implementation: `app/bie/compiler/narration_consumer.py`. Complete batch interfaces, bounds, producer/consumer behavior, timing and rejection policy are in `docs/COMP_H6_SPEC.md`.

Verification: `tests/compiler/test_comp_h6_004.py`; 22 local atomic tests. Run only after the complete H6 workspace has been restored, because task suites also exercise adopted producer/consumer paths. Ten cross-task tests are separately in `tests/compiler/test_comp_h6_integration.py`.

Evidence: real Python/Node processes and installed TypeScript; real local PCM bytes for asset cases; labelled React/Remotion API doubles for browser/component behavior. None of these task counts certify a full pinned-project compile, actual Remotion rendering, spoken narration alignment, educational value, or product acceptance.

Original H5 source and historical fixtures are retained. Changes to inherited code are escrowed under `lineage/hardening_h5/originals/`. Restore is additive/replace-only, with exact file preconditions and ordered tree identities. No GitHub write is part of this task.
