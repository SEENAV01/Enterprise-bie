# BIE-QA-HARD-024 — End-to-end accessibility gate

Owner: QA.VIS.GAME. Local namespace: `bie/qa/lifecycle_quality_v2`.

## Original scope (preserved)
Assemble real output accessibility checks across visual, motion, narration, caption and game controls with explicit applicability.

## Required full-closure evidence (preserved)
- Keyboard/focus, color-independent meaning, readable labels and captions have failing controls.
- Reduced-motion and flash checks cover actual output, not only the plan.
- No blanket conformance certificate from static style metadata.

## Local implementation
Actual-output accessibility evidence aggregation and static keyboard/focus capture. Exact required viewports/controls/caption/meaning inventories, byte/time bindings and unmeasured-axis review.

## Inputs, outputs and trust
All mutable target paths, required validators, policies, source/fixture inventories and authority are operator inputs. Candidate/document text cannot grant privileges, weaken gates or authorize its own changes. Reports/receipts identify exact artifact bytes, run, revision, candidate and policy. Proposed fixes do not modify the original and cannot inherit old signatures.

## Executed test/evidence locations
- `tests/qa_hardening_h6/test_accessibility.py`
- `tests/qa_hardening_h6/test_schemas_cli.py`
- `hardening/section16_h6/evidence/final_source_suites/TEST_RESULT.json`
- `hardening/section16_h6/evidence/mutations/MUTATION_RESULT.json`
- `hardening/section16_h6/evidence/diagnostics/EXECUTION_RESULT.json`

The 137-case H6 suite is shared, not an independent count per task. Positive review credentials and human/model observations are explicitly synthetic.

## Remaining requirements
- Native final audiovisual and game output, screen-reader/focus behavior, actual caption paint and motion/flash coverage remain open.
- Static desktop keyboard fixtures are not WCAG conformance, physical-device support, whole-film flash analysis or clinical certification.

No historical obligation is closed here. Section15, GitHub and global continuation are unchanged. Final section audit and canonical real-book gates remain required.
