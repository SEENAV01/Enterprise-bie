# H9 Re-audit

H9 closes the principal **implementation-framework gaps** remaining in AUDIO-AUDIT-001-F02:
1. provider-neutral multilingual/accent/IPA/OOV evaluator capability negotiation is explicit and fail-closed;
2. modern evaluator request/report contracts bind current delivered media, exact reading/source targets, voice/model/runtime identity, coverage and uncertainty;
3. a held-out calibration harness measures false-positive/false-negative behavior and cannot hide insufficient coverage or uncertainty;
4. signed evaluator release authority is separate from evaluator output and requires a trusted production issuer plus external KMS/HSM custody claim and held-out independent calibration before production authorization;
5. governed decisions block/review insufficient authority or uncertainty, and calibrated failures create unchanged-reading downstream invalidation intents without claiming dispatch.

Fresh H9 focused tests: **69/69 PASS**. Existing H2 diagnostic contract compatibility: **120/120 PASS** (H2-001..004 = 99; H2-005 = 21). Combined targeted evidence: **189/189 PASS**.

These tests include generated labels and ephemeral signing keys; they validate contracts, not real evaluator quality. No live multilingual/accent evaluator, independent human listener panel, neural production speech calibration, real-book corpus, HSM/KMS deployment, or rendered lecture evidence was supplied. Therefore F02 external validation remains open and section acceptance is not permitted.

Remaining material implementation work before final AUDIO regression: **F04 canonical DIR narration → AUDIO → ANI/COMP handoff, repair-driven invalidation, pinned compile/render and rendered AV/caption evidence.** External/live F01/F02/F03 deployment evidence remains an acceptance gate and must not be invented.
