# BIE-QA-HARD-017 — Native visual and rendered-content correspondence

## Original audit scope
Bind required diagrams, equations, text and references to actual frames/DOM at required viewports, including complex paint and occlusion coverage.

## Original closure obligations (preserved)
- Missing/cropped/occluded labels and changed scientific relationships fail.
- Measurements cannot be edited to repair evidence; recapture is required.
- Renderer/runtime/asset provenance is checked, not just PNG decodability.

## Implemented local behavior
Executes native LayoutPlan validation and actual controlled Chromium static measurements/screenshots; binds HTML/PNG bytes and viewport, compares required text/geometry and spatial relations, checks boundary/ancestor clipping and sampled hit-test occlusion. Supplied observations never count as new captures.

## Remaining operational scope
- Static trusted HTML about:blank samples are not native Remotion/game execution or final audiovisual proof.
- Five-point hit testing can miss partial/pointer-events:none occlusion; arbitrary paint/3D/continuous-frame correspondence, trusted capture attestation and production sandbox integration remain open.

## Source and evidence
- `bie/qa/domain_quality_v2/common.py`
- `bie/qa/domain_quality_v2/visual.py`

Shared test suite: `tests/qa_hardening_h4` (211 unique methods across all six tasks; do not multiply). Executed receipt: `hardening/section16_h4/evidence/final_source_suites/TEST_RESULT.json`. Mutation and diagnostic receipts are adjacent under `evidence/`. Specifications do not substitute for those executions.

## Integration boundary
Native APIs and original source artifacts remain unchanged. This is additive local code with full local regression, not canonical repository integration. No production PASS/certificate, source semantic clearance or learner mastery is issued. All 113 historical/audit obligations remain authoritative; none is closed by this task.
