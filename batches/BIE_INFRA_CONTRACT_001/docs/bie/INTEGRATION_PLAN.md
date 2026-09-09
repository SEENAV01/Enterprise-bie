# Integration Plan into existing repository

1. Add `app/bie/bie_core/artifact_contracts.py`.
2. Keep existing domain dataclasses temporarily; wrap their outputs in `ArtifactEnvelope`.
3. First migration sequence:
   - document_ingestor -> source.document/source.block envelopes
   - concept_understanding -> knowledge.concept / prerequisite.graph envelopes
   - future reasoning engine -> reasoning.decision envelopes
   - lesson/director/visual/animation -> typed plan envelopes
   - Scene IR / Game IR -> typed envelopes
   - generated code -> code.bundle envelope
   - compile/render/runtime -> execution.evidence envelopes
   - QA -> qa.evidence envelopes
   - release -> release.manifest envelope
4. Do not break current M001-M301 flow in one commit. Add compatibility adapters, characterize behavior, then migrate stage-by-stage.
5. Release status must later be computed only from verified evidence graph.
