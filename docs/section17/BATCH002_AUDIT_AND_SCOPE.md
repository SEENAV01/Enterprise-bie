# Batch002 audit and evidence limits

The first 374-method run failed 18 methods, due to the shared quantity-conversion defect and downstream checks. The expanded 474-method adversarial run failed 27 methods and had one test-selection error. After fixes all 474 passed. A later 492-method contract run had one registry-key test error; its correction plus the fixture-rebuild test yielded **493/493**, zero failures/errors/skips. All intermediate receipts and preimages are preserved under `evidence/section17/batch002/`. Failed runs are history, not the final candidate verdict.

The three implementation/model/provenance findings and two test-authoring corrections are separately classified in `BATCH002_AUDIT_FINDINGS.json`. Eight injected reference faults were caught by the named tests; restored behavior passed. This is fault sensitivity, not real BIE performance or complete mutation coverage. Repeated executions are not extra test methods.

The 180-case diagnostic is the real local registry -> immutable snapshot -> frozen roster -> structured calculator/grader -> persistent SQLite report path. It is reference replay against authored expectations, **not** an independent golden benchmark, a native PDF-to-video/game run or a measured learner outcome. Corpus review, real inputs, native integration and all later release gates remain required.
