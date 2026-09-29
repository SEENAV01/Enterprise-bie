# Atomic work/evidence map

| Original task | Main implementation | Shared prerequisites | Executed evidence |
|---|---|---|---|
| BIE-QA-PR-001 | prerequisite.py | source_v2, native PR graph, review authentication | test_pr_proofs.PrerequisiteTests; test_logic_models; I/O/trust/schema suites |
| BIE-QA-RE-001 | logic.py, proofs.py | typed claims, mapping/inference reviews | LogicTests, ProofTests, trust and schema suites |
| BIE-QA-RE-002 | evidence.py | source_v2, operator lineage, authenticated support | EvidenceTests plus source regression and trust suites |
| BIE-QA-RE-003 | calibration.py, uncertainty.py | actual support bytes, native RE diagnostics | CalibrationTests, UncertaintyTests, bridge and trust suites |

Shared infrastructure: models.py, codec.py, attestation.py, context.py, evaluator.py,
adapters.py, bridge.py, CLI. Four per-task TASK_RESULT files point to one shared test
receipt. Do not multiply 217 by four or treat 273 included subcases as extra tests.

Verified sequence: recover/pin parent; enumerate exact registry scope; preserve parent
metadata/source; inspect native interfaces; define closed contracts; implement/evaluate;
add positive and adversarial tests; inspect failures; fix against real APIs; add schema
validation; run full new suite; run inherited suite; run targeted fault-removal controls;
execute unsigned demo; record limits; update only local QA continuation/gaps; document
integration safeguards; create deterministic packages; extract and rerun; verify manifests
and corruption rejection; preserve backup lineage and publish exact archive identities.
Final packaging/replay evidence is recorded in the delivery receipt, outside the ZIPs.
