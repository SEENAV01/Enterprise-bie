# BIE-QA-HARD-011 — Prerequisite readiness and applicability adapter

## Original audit requirement
Bind approved learner/context prerequisites and justified task applicability to actual lessons and runtime outputs.

## Implemented local scope
Consumes the actual preserved PrerequisiteGraph and source-QA request. Computes transitive requirements and checks all authoritative lesson routes. Learner diagnostic bytes bind learner, policy, observations, criterion floors and timestamps; synthetic/unverified observations cannot confer mastery. Failing evidence cannot be outvoted. Applicability requests retain all mandatory gate IDs.

## Executed / tested behavior
- Cycles, inconsistent edges, wrong alternate-route order, learner mismatch, stale diagnostics and criterion-floor violations are tested.
- The native prerequisite/source path is executed in an authored diagnostic.
- No-math requests never remove release gates or fabricate domain proof.

## Required closure still open
- Actual learner measurements and observed native lesson/game behavior remain OPEN.
- Positive observed-evidence unit fixtures have synthetic credentials and labels; they are not genuine learners.
- Grounded independent applicability approval and full canonical lesson integration remain required.

This task has a local adapter/interface implementation, not full operational closure. Source files and old evaluations are never rewritten to create a pass. No release is authorized. Read the shared execution receipts; do not multiply shared test counts by five.
