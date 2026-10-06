"""Eight-stage producer delegates DIRECTOR to the hardened production assembly.

Outer SQLitePersistence is the pipeline authority. Native Director databases
are its existing stage-internal journal/claims/revisions/leases, over the same
CAS. No model quality or exactly-once external invocation guarantee is made.
"""
from dataclasses import asdict
from types import SimpleNamespace

from bie.bie_core.artifact_contracts import ArtifactRef
from bie.infrastructure.artifact_store import BlobRef
from bie.infrastructure.orchestrator import StageExecutionResult, StageExecutionFailure
from bie.director.director_artifacts import envelope_from_dict, reference
from bie.director.director_executor import DirectorStageExecutor
from bie.director.production_adoption import DirectorProductionRequest, ProductionSceneCorrection
from bie.director.contextual_teaching import _present
from .contracts import require, ProducerError, strict_json, digest, canonical
from .pedagogy_slice import PedagogyProducerService, STAGES as PEDAGOGY_STAGES
from .director_contract import PROFILE, SCHEMA, POLICY, profile_config, run_identity, native_key
from .director_storage import (native_runtime, import_native_result, native_record,
                              OrderedProducerArtifactCatalog, DirectorReadPersistence)

STAGES = PEDAGOGY_STAGES + ("DIRECTOR",)


def admit_native_result(assembly, request, result, components, math):
    """Run actual native consumer validation; additionally require all transports.

    Native component review permits incomplete critic evidence. This producer's
    governed execution contract requires the configured critic/reviewer to have
    completed, while never upgrading their judgments to academic acceptance.
    """
    require(len(result.output_artifact_refs) == 1, "director_output_contract")
    output, execution = assembly.consumers()._director(result.output_artifact_refs[0])
    require(output.payload["schema_version"] == SCHEMA, "director_schema_mismatch")
    require(output.run_id == request.run_id and output.payload["lesson_id"] == request.lesson_id,
            "director_foreign_run")
    require({request.reasoning_ref, request.pedagogy_ref} <= set(output.parent_refs),
            "director_upstream_identity")
    require(output.metadata.get("requires_review") is True and
            output.metadata.get("accepted") is False and output.metadata.get("release_ready") is False,
            "director_review_boundary")
    evidence = assembly.io.load(reference(output.payload["execution_evidence_ref"]))
    raw = evidence.payload["result"]
    require("base_result" in raw and "annotation_production" in raw and "annotation_review" in raw,
            "director_annotations_required")
    for semantic in (raw["base_result"]["semantic_evaluation"], raw["semantic_evaluation"]):
        require(not semantic["failures"], "director_critic_execution_incomplete")
        require(semantic["attempts"] and semantic["receipts"], "director_critic_execution_incomplete")
    require(not raw["annotation_review"]["failures"] and raw["annotation_review"]["attempts"],
            "director_annotation_review_incomplete")
    require(raw["annotation_production"]["attempts"], "director_annotations_required")
    # No context-free model may invent or waive an upstream mathematical step.
    # Task032 provides EXPLANATION only; derivation-specific material is gated
    # before invocation until canonical upstream teaching obligations exist.
    utterances = execution.snapshot.utterances
    for equation in math["equations"]:
        require(any(equation["anchor_id"] in u.evidence_ids and
                    _present(equation["original_expression"], u.text, mathematical=True)
                    for u in utterances), "director_math_obligation_missing")
    return output, evidence, raw, execution


class DirectorProducerService(PedagogyProducerService):
    stages = STAGES
    profile = PROFILE
    capability = "producer:" + PROFILE
    completion_stage = "DIRECTOR"
    identity_for = staticmethod(run_identity)
    config_for = staticmethod(profile_config)
    director_input_catalog = OrderedProducerArtifactCatalog
    persistence_factory = DirectorReadPersistence
    downstream = tuple(s for s in PedagogyProducerService.graph_for().stages if s not in STAGES)
    blocked_codes = PedagogyProducerService.blocked_codes | frozenset({
        "director_provider_unavailable", "director_math_teaching_contract_required"})

    def __init__(self, *args, director_stack=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.director_stack = director_stack

    def canonical_config(self, config):
        return profile_config(config["provider"], config["model"], director=config.get("director"))

    def close(self):
        try:
            self.persistence.close()
        finally:
            super().close()

    def record(self, run_id, artifact_id):
        row = self.persistence.load_artifact(artifact_id)
        if ":" not in artifact_id:
            return super().record(run_id, artifact_id)
        native_record(self, run_id, row)
        return row

    def request(self, run, tenant):
        config = self.configuration(run, tenant)
        aid, row, value, components, _ = self.verified_pedagogy(run, tenant)
        env = envelope_from_dict(value)
        rp = ArtifactRef(**env.payload["reasoning_ref"])
        settings = config["config"]["director"]
        request = DirectorProductionRequest(run, native_key(run, rp, env.to_ref(), settings),
            settings["revision"], components["plan"]["lesson_ids"][0], settings["title"],
            settings["language"], rp, env.to_ref(), settings["previous_key"],
            tuple(ProductionSceneCorrection(c["scene_id"], tuple(c["reasons"]))
                  for c in settings["scene_corrections"]))
        request.validate()
        return request, components, aid

    def executor(self, config, stage, lease):
        if stage != "DIRECTOR":
            return super().executor(config, stage, lease)
        def execute(context):
            try:
                run = context.run_id
                request, components, ped_id = self.request(run, config["tenant"])
                re_id = components["upstream"]["reasoning"]["artifact_id"]
                require(context.input_artifact_refs == [ped_id, re_id], "director_upstream_identity")
                _, math = self.verified_math(run, config)
                require(not math["derivation_steps"], "director_math_teaching_contract_required")
                require(self.director_stack is not None, "director_provider_unavailable")
                require(self.director_stack.descriptor() == config["config"]["director"]["providers"] and
                        self.director_stack.evidence_kind == config["config"]["director"]["evidence_kind"],
                        "director_provider_identity_mismatch")
                require(canonical(asdict(self.director_stack.annotations.policy)) ==
                        canonical(config["config"]["director"]["annotation_policy"]) and
                        canonical(asdict(self.director_stack.annotations.review_policy)) ==
                        canonical(config["config"]["director"]["annotation_review_policy"]),
                        "director_policy_conflict")
                with native_runtime(self, run, self.director_stack) as assembly:
                    # Canonical registration is checked alongside outer graph.
                    definitions, executors = assembly.register({}, {})
                    require(definitions[stage].output_type == "director.plan" and
                            executors[stage] is assembly.executor, "director_registration_invalid")
                    assembly.context(request)
                    self.fault("after_DIRECTOR_input_validation")
                    result = assembly.execute(request)
                    self.fault("after_DIRECTOR_native_execution")
                    output, evidence, raw, execution = admit_native_result(assembly, request, result, components, math)
                    import_native_result(self, run, assembly.io.catalog,
                        result.output_artifact_refs + result.evidence_refs)
                    receipt = dict(schema="bie.producer.stage-evidence/1", run_id=run, stage=stage,
                        profile=PROFILE, policy=POLICY, attempt=context.attempt,
                        native_attempt=request.attempt, native_intent_sha256=digest(config["config"]["director"]),
                        source_sha256=config["source_sha256"], input_artifact_ids=context.input_artifact_refs,
                        input_sha256=[self.record(run, r).blob_digest for r in context.input_artifact_refs],
                        native_reasoning_ref=asdict(request.reasoning_ref), native_pedagogy_ref=asdict(request.pedagogy_ref),
                        math_artifact_id=components["upstream"]["math"]["artifact_id"],
                        math_sha256=components["upstream"]["math"]["sha256"],
                        output_artifact_id=output.artifact_id, output_sha256=self.record(run, output.artifact_id).blob_digest,
                        envelope_hash=output.content_hash, schema_version=SCHEMA,
                        native_execution_evidence_ref=asdict(evidence.to_ref()),
                        providers=self.director_stack.descriptor(),
                        code_identity=raw["base_result"]["code_fingerprint"],
                        generation_attempt_count=len(raw["base_result"]["generation_attempts"]),
                        critic_attempt_count=sum(len(v["attempts"]) for v in
                            (raw["base_result"]["semantic_evaluation"], raw["semantic_evaluation"])),
                        annotation_attempt_count=len(raw["annotation_production"]["attempts"]),
                        review_attempt_count=len(raw["annotation_review"]["attempts"]),
                        scene_count=len(output.payload["plan"]["scenes"]),
                        beat_count=len(execution.snapshot.utterances),
                        assessment_count=len(output.payload["assessment_bindings"]),
                        validation="PASS", grounding="NATIVE_CANONICAL_DIRECTOR_QA_EXECUTED",
                        requires_review=True, accepted=False, release_ready=False,
                        director_executed=True, visual_executed=False, audio_complete=False,
                        fencing_epoch=lease.epoch, evidence_kind=self.director_stack.evidence_kind,
                        configured_provider_invoked=self.director_stack.evidence_kind != "SYNTHETIC_TEST",
                        # An injected provider identity alone cannot establish
                        # whether its transport actually called a live service.
                        live_provider_executed=False if self.director_stack.evidence_kind == "SYNTHETIC_TEST" else None,
                        academic_acceptance=False, product_accepted=False)
                    safe = self.put(run, stage, "producer.evidence", receipt,
                        context.input_artifact_refs + [output.artifact_id], True)
                self.write_guard()
                return StageExecutionResult([output.artifact_id], [safe])
            except StageExecutionFailure as failure:
                code = failure.diagnostics[0] if len(failure.diagnostics) == 1 else "director_execution_failed"
                safe = self.put(context.run_id, stage, "producer.failure", dict(
                    schema="bie.producer.failure/1", code=code, stage=stage,
                    attempt=context.attempt, product_accepted=False), evidence=True)
                raise StageExecutionFailure([code], [safe], "PROD033") from None
            except Exception as exc:
                code = exc.code if isinstance(exc, ProducerError) else "director_execution_failed"
                safe = self.put(context.run_id, stage, "producer.failure", dict(
                    schema="bie.producer.failure/1", code=code, stage=stage,
                    attempt=context.attempt, product_accepted=False), evidence=True)
                raise StageExecutionFailure([code], [safe], "PROD033") from None
        return execute

    def verified_director(self, run, tenant):
        config = self.configuration(run, tenant)
        request, components, _ = self.request(run, tenant)
        aid, record = self.stage_ref(run, "DIRECTOR")
        # Validation never needs or calls a configured live provider.
        with native_runtime(self, run, None) as assembly:
            output = assembly.io.load(aid)
            from bie.director.director_consumers import DirectorConsumers
            from bie.director.director_revisions import DirectorRevisionStore
            consumers = DirectorConsumers(assembly.io, DirectorRevisionStore(assembly.idempotency))
            output, execution = consumers._director(output.to_ref())
            evidence = assembly.io.load(reference(output.payload["execution_evidence_ref"]))
            raw = evidence.payload["result"]
            require(not raw["base_result"]["semantic_evaluation"]["failures"] and
                    not raw["semantic_evaluation"]["failures"] and
                    not raw["annotation_review"]["failures"], "director_evaluation_incomplete")
            settings = config["config"]["director"]
            require(evidence.payload["generator"] == settings["providers"]["generator"] and
                    evidence.payload["critic"] == settings["providers"]["critic"] and
                    evidence.payload["annotation_runtime"]["annotator"] == settings["providers"]["annotator"] and
                    evidence.payload["annotation_runtime"]["reviewer"] == settings["providers"]["reviewer"],
                    "director_provider_identity_mismatch")
            claim = assembly.idempotency.get(request.idempotency_key)
            require(claim.state == "COMPLETED" and claim.fingerprint ==
                    output.metadata["execution_fingerprint"], "director_native_commit_missing")
            # Status/recovery must verify the native replay record too, not
            # report success from an orphaned output after claim/CAS tampering.
            # Reuse the executor's actual parser, contract and ancestry checks;
            # this read-only view constructs no provider or second executor.
            replay_reader = SimpleNamespace(io=assembly.io)
            replay_reader._read_blob = lambda ref: DirectorStageExecutor._read_blob(replay_reader, ref)
            try:
                replay = DirectorStageExecutor._replay(replay_reader, claim.result_ref, claim.fingerprint)
            except Exception:
                raise ProducerError("director_native_replay_mismatch") from None
            require(replay.output_artifact_refs == [aid] and
                    replay.evidence_refs == [evidence.artifact_id] and
                    replay.metadata == output.metadata and
                    replay.diagnostics == ["DIRECTOR_COMPONENT_EXECUTED_REVIEW_REQUIRED"],
                    "director_native_replay_mismatch")
            require(output.payload["schema_version"] == SCHEMA and
                    {request.reasoning_ref, request.pedagogy_ref} <= set(output.parent_refs),
                    "director_upstream_identity")
            snapshot = self.persistence.load_run_state(run)["stages"]["DIRECTOR"]["attempts"][-1]
            require(len(snapshot["evidence_refs"]) == 1, "director_receipt_mismatch")
            receipt = self.read(run, snapshot["evidence_refs"][0])
            require(receipt["output_artifact_id"] == aid and receipt["output_sha256"] == record.blob_digest
                    and receipt["native_reasoning_ref"] == asdict(request.reasoning_ref)
                    and receipt["native_pedagogy_ref"] == asdict(request.pedagogy_ref)
                    and receipt["native_intent_sha256"] == digest(settings)
                    and receipt["providers"] == settings["providers"]
                    and receipt["code_identity"] == raw["base_result"]["code_fingerprint"],
                    "director_receipt_mismatch")
            return output, receipt

    def status(self, run, tenant):
        result = super().status(run, tenant)
        result["director"] = None
        if result["stages"]["DIRECTOR"] == "SUCCEEDED":
            output, receipt = self.verified_director(run, tenant)
            result["director"] = {k: receipt[k] for k in ("output_artifact_id", "output_sha256",
                "schema_version", "scene_count", "beat_count", "assessment_count",
                "generation_attempt_count", "critic_attempt_count", "annotation_attempt_count",
                "review_attempt_count", "requires_review", "accepted", "release_ready", "evidence_kind")}
            result["director"].update(validation="PASS", director_executed=True,
                                      visual_input_validator="NOT_AVAILABLE_FOR_NATIVE_ARTIFACT_PAIR")
            result["live_provider_executed"] = receipt["live_provider_executed"]
            result["configured_provider_invoked"] = receipt["configured_provider_invoked"]
        return result
