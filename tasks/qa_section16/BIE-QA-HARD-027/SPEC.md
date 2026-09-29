# BIE-QA-HARD-027 — Native generated-code and game repair integration

Owner: COMP.GAME.QA. Local namespace: `bie/qa/lifecycle_quality_v2`.

## Original scope (preserved)
Apply owner-scoped repairs to actual generated modules using approved templates/transformations rather than claiming universal code repair.

## Required full-closure evidence (preserved)
- Handwritten code/tests/policies are protected.
- Compile and native runtime validation are required after repair.
- Defects outside the supported transformation set escalate with intact originals.

## Local implementation
Owner/recipe/SceneIR/emitter-bound complete JSON-literal slot transformations in explicitly generated TypeScript const-data modules. Protects all other bytes and requires compile/native-runtime/regression check scope before controller handoff.

## Inputs, outputs and trust
All mutable target paths, required validators, policies, source/fixture inventories and authority are operator inputs. Candidate/document text cannot grant privileges, weaken gates or authorize its own changes. Reports/receipts identify exact artifact bytes, run, revision, candidate and policy. Proposed fixes do not modify the original and cannot inherit old signatures.

## Executed test/evidence locations
- `tests/qa_hardening_h6/test_repairs.py`
- `tests/qa_hardening_h6/test_handoff.py`
- `tests/qa_hardening_h6/test_schemas_cli.py`
- `hardening/section16_h6/evidence/final_source_suites/TEST_RESULT.json`
- `hardening/section16_h6/evidence/mutations/MUTATION_RESULT.json`
- `hardening/section16_h6/evidence/diagnostics/EXECUTION_RESULT.json`

The 137-case H6 suite is shared, not an independent count per task. Positive review credentials and human/model observations are explicitly synthetic.

## Remaining requirements
- This is a restricted data-module adapter, not arbitrary TypeScript/React/game-interface repair. Unsupported module grammar or handwritten functions escalate.
- Actual TypeScript and Node diagnostics ran, but native BIE generated application repair, full rebuild and native-origin runtime did not; H5 native runtime gates remain open.

No historical obligation is closed here. Section15, GitHub and global continuation are unchanged. Final section audit and canonical real-book gates remain required.
