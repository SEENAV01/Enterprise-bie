"""Eleven-stage delegation using existing durable stores and fenced publication."""
from dataclasses import asdict
from bie.infrastructure.orchestrator import EnterpriseOrchestrator, StageExecutionResult, StageExecutionFailure
from bie.infrastructure.artifact_store import BlobRef
from bie.scene_ir.replay_currentness import DSLVersionVector, make_replay_record, evaluate_currentness, require_current
from bie.scene_ir.unified_scene_ir_codec import encode_scene_ir
from bie.compiler.scene_ir_loader import load_scene_ir_payload
from .animation_slice import AnimationProducerService, STAGES as ANIMATION_STAGES
from .contracts import require, ProducerError, canonical, digest, sha
from .scene_ir_contract import PROFILE, POLICY, SCHEMA, profile_config, run_identity, refresh_code_identity, strict_document
from .scene_ir_plan import build_current_scene

STAGES = ANIMATION_STAGES + ("SCENE_IR",)
INPUT_STAGES = ("VISUAL", "ANIMATION", "DIRECTOR")
FAILURE_CODES = frozenset({"scene_ir_multiple_scenes_unsupported", "scene_ir_audio_replan_required",
    "scene_ir_structure_unsupported", "scene_ir_text_overflow", "scene_ir_domain_unsupported",
    "scene_ir_capability_blocked", "scene_ir_presentation_bounds", "scene_ir_upstream_identity",
    "scene_ir_mapping_tampered", "scene_ir_node_plan_mismatch", "scene_ir_parent_identity",
    "scene_ir_handoff_contract", "scene_ir_adoption_field_loss", "scene_ir_adoption_track_loss",
    "scene_ir_codec_conservation", "scene_ir_loader_mismatch", "scene_ir_consumer_layout_blocked",
    "scene_ir_motion_selection_conservation", "scene_ir_native_validators_incomplete",
    "scene_ir_execution_failed"})


def safe_failure_code(exc):
    # Even a ProducerError supplied by an extension/fault hook cannot export a
    # private exception message as its code. Native diagnostics stay private.
    # Subclasses can override attribute access and change the value between
    # validation and publication. Admit only the trusted native exception and
    # snapshot its plain data once; never evaluate a hostile subclass property.
    if type(exc) is not ProducerError:
        return "scene_ir_execution_failed"
    try:
        code = exc.code
    except Exception:
        return "scene_ir_execution_failed"
    return code if type(code) is str and code in FAILURE_CODES else "scene_ir_execution_failed"


class SceneIRInputOrchestrator(EnterpriseOrchestrator):
    """Compose the declared consumed Director input without changing predecessors.

    This is a profile-local input resolver, not a second worker/control plane.
    All scheduling, transition, persistence and lease code remains canonical.
    """
    def _resolve_inputs(self, stage_id):
        if stage_id != "SCENE_IR":
            return super()._resolve_inputs(stage_id)
        require(self.definitions[stage_id].input_types == ["visual.plan", "animation.plan", "director.plan"],
                "scene_ir_global_contract")
        refs = []
        for predecessor in INPUT_STAGES:
            require(self.state.stages[predecessor].current.state == "SUCCEEDED", "scene_ir_predecessor")
            out = self.artifacts.outputs_for_stage(self.state.run_id, predecessor)
            require(len(out) == 1, "scene_ir_input_cardinality")
            refs.extend(out)
        return refs


class SceneIRProducerService(AnimationProducerService):
    stages = STAGES
    profile = PROFILE
    capability = "producer:" + PROFILE
    completion_stage = "SCENE_IR"
    config_for = staticmethod(profile_config)
    identity_for = staticmethod(run_identity)
    orchestrator_type = SceneIRInputOrchestrator
    downstream = tuple(s for s in AnimationProducerService.graph_for().stages if s not in STAGES)
    blocked_codes = AnimationProducerService.blocked_codes | frozenset({"scene_ir_multiple_scenes_unsupported",
        "scene_ir_audio_replan_required", "scene_ir_structure_unsupported", "scene_ir_text_overflow",
        "scene_ir_domain_unsupported", "scene_ir_capability_blocked", "scene_ir_presentation_bounds"})

    def canonical_config(self, config):
        return profile_config(config["provider"], config["model"], director=config.get("director"),
            visual=config.get("visual"), animation=config.get("animation"), scene_ir=config.get("scene_ir"))

    def stage_input_refs(self, run, stage):
        if stage != "SCENE_IR":
            return super().stage_input_refs(run, stage)
        return [self.stage_ref(run, s)[0] for s in INPUT_STAGES]

    def require_parents(self, run, artifact_id, expected):
        actual = self.record(run, artifact_id).parent_artifact_ids
        require(len(actual) == len(set(actual)) and set(actual) == set(expected), "scene_ir_parent_identity")

    def verify_terminal_for_ack(self, run, tenant):
        refresh_code_identity()
        super().verify_terminal_for_ack(run, tenant)
        state = self.persistence.load_run_state(run)["stages"]["SCENE_IR"]["attempts"][-1]["state"]
        if state == "SUCCEEDED":
            self.verified_scene_ir(run, tenant)

    def _parents(self, run, bundle, animation_receipt):
        return self.stage_input_refs(run, "SCENE_IR") + [
            animation_receipt[k] for k in ("current_inputs_id", "validation_id", "handoff_id")] + [
            bundle["visual_receipt"][k] for k in ("current_inputs_id", "validation_id", "handoff_id")] + [
            bundle["candidate"].artifact_id, bundle["visual_receipt"]["sync_ref"]["artifact_id"]]

    def _replay_scene(self, run, document, private, parents):
        require(len(set(parents)) == len(parents), "scene_ir_dependency_duplicates")
        settings = self.configuration(run, self.read(run, run + "-config")["tenant"])["config"]["scene_ir"]
        deps = {p: self.record(run, p).blob_digest for p in parents}
        vector = DSLVersionVector(document.upstream_revision, SCHEMA, settings["capability_profile"],
            digest(dict(dependencies=deps, mapping=private["catalog_mapping"], engines=settings["engines"],
                motion=private["motion_admission_id"], scope=private["scope"])), digest([]))
        record = make_replay_record(document, digest(dict(private=private, settings=settings, dependencies=deps)), vector, deps)
        require(set(dict(record.dependency_fingerprints)) == set(deps), "scene_ir_dependency_set")
        require_current(evaluate_currentness(record, document, vector, deps))
        return asdict(record)

    def _receipt(self, run, config, attempt, document, private, parents, output, inputs, validation, epoch):
        return dict(schema="bie.producer.stage-evidence/1", run_id=run, stage="SCENE_IR", profile=PROFILE,
            policy=POLICY, attempt=attempt, source_sha256=config["source_sha256"],
            input_artifact_ids=self.stage_input_refs(run, "SCENE_IR"),
            input_sha256=[self.record(run, p).blob_digest for p in self.stage_input_refs(run, "SCENE_IR")],
            output_artifact_id=output, output_sha256=self.record(run, output).blob_digest,
            schema_version=SCHEMA, document_fingerprint=document.fingerprint,
            current_inputs_id=inputs, validation_id=validation, replay=self._replay_scene(run, document, private, parents),
            element_count=len(document.elements), track_count=len(document.tracks), native_validator_count=7,
            single_scene=True, validation="PASS", compiler_loader_admitted=True,
            requires_review=True, accepted=False, release_ready=False, product_accepted=False,
            audio_complete=False, audio_reconciliation_open=True, scene_ir_executed=True,
            video_code_executed=False, evidence_kind="TECHNICAL_SOURCE_DERIVED", fencing_epoch=epoch)

    def executor(self, config, stage, lease):
        if stage != "SCENE_IR":
            return super().executor(config, stage, lease)
        def execute(context):
            run = context.run_id
            try:
                require(context.input_artifact_refs == self.stage_input_refs(run, stage), "scene_ir_upstream_identity")
                document, private, bundle, animation_receipt = build_current_scene(self, run, config["tenant"], fault=self.fault)
                parents = self._parents(run, bundle, animation_receipt)
                with self.publication_guard(run, bundle["director"]):
                    inputs = self.put(run, stage, "scene_ir.current_inputs", dict(policy=POLICY,
                        input_artifact_ids=context.input_artifact_refs,
                        dependency_sha256={p: self.record(run, p).blob_digest for p in parents},
                        settings=config["config"]["scene_ir"], private=private), parents)
                    validation = self.put(run, stage, "scene_ir.validation", private, parents + [inputs])
                    self.fault("after_SCENE_IR_private_publication")
                    output = self.put(run, stage, "scene.ir", document.to_dict(), parents + [inputs, validation])
                    # Consume the EXACT persisted bytes, not a reconstructed equivalent.
                    self._load_persisted(run, output, document)
                    receipt = self._receipt(run, config, context.attempt, document, private, parents,
                        output, inputs, validation, lease.epoch)
                    safe = self.put(run, stage, "producer.evidence", receipt, parents + [output], True)
                    self.write_guard()
                    self.fault("before_SCENE_IR_terminal")
                return StageExecutionResult([output], [safe])
            except Exception as exc:
                code = safe_failure_code(exc)
                safe = self.put(run, stage, "producer.failure", dict(schema="bie.producer.failure/1",
                    code=code, stage=stage, attempt=context.attempt, product_accepted=False), evidence=True)
                raise StageExecutionFailure([code], [safe], "PROD036") from None
        return execute

    def _load_persisted(self, run, ref, expected):
        row = self.record(run, ref)
        require(row.stage_id == "SCENE_IR" and row.artifact_type == "scene.ir" and not row.evidence,
                "scene_ir_output_identity")
        raw = self.cas.get_bytes(BlobRef(row.blob_algorithm, row.blob_digest, row.blob_size))
        document = strict_document(raw)
        require(document.to_dict() == expected.to_dict(), "scene_ir_output_tampered")
        loaded = load_scene_ir_payload(raw.decode("utf-8"))
        require(loaded.source_sha256 == row.blob_digest == sha(raw) and
            loaded.scene_fingerprint == document.fingerprint and
            loaded.canonical_json == encode_scene_ir(document) and loaded.validation_passed and loaded.accepted is False,
            "scene_ir_persisted_loader_mismatch")
        return document

    def verified_scene_ir(self, run, tenant):
        config = self.configuration(run, tenant)
        ref, row = self.stage_ref(run, "SCENE_IR")
        attempt = self.persistence.load_run_state(run)["stages"]["SCENE_IR"]["attempts"][-1]
        require(attempt["input_artifact_refs"] == self.stage_input_refs(run, "SCENE_IR") and
                len(attempt["evidence_refs"]) == 1, "scene_ir_committed_identity")
        safe = self.record(run, attempt["evidence_refs"][0])
        require(safe.stage_id == "SCENE_IR" and safe.artifact_type == "producer.evidence" and safe.evidence is True
            and safe.metadata.get("privacy") == "SAFE_EVIDENCE", "scene_ir_receipt_identity")
        receipt = self.read(run, safe.artifact_id)
        document, private, bundle, animation_receipt = build_current_scene(self, run, tenant)
        parents = self._parents(run, bundle, animation_receipt)
        for aid, kind, expected_parents, expected in (
            (receipt["current_inputs_id"], "scene_ir.current_inputs", parents,
                dict(policy=POLICY, input_artifact_ids=attempt["input_artifact_refs"],
                    dependency_sha256={p: self.record(run, p).blob_digest for p in parents},
                    settings=config["config"]["scene_ir"], private=private)),
            (receipt["validation_id"], "scene_ir.validation", parents + [receipt["current_inputs_id"]], private)):
            record = self.record(run, aid)
            require(record.stage_id == "SCENE_IR" and record.artifact_type == kind and not record.evidence,
                    "scene_ir_support_identity")
            self.require_parents(run, aid, expected_parents)
            require(canonical(self.read(run, aid)) == canonical(expected), "scene_ir_support_tampered")
        self.require_parents(run, ref, parents + [receipt["current_inputs_id"], receipt["validation_id"]])
        self.require_parents(run, safe.artifact_id, parents + [ref])
        self._load_persisted(run, ref, document)
        expected = self._receipt(run, config, attempt["attempt"], document, private, parents, ref,
            receipt["current_inputs_id"], receipt["validation_id"], receipt["fencing_epoch"])
        require(canonical(receipt) == canonical(expected), "scene_ir_receipt_mismatch")
        lease = self.leases.get(self.task_id(run, "SCENE_IR", attempt["attempt"]))
        require(lease.fingerprint == config["fingerprint"] and type(receipt["fencing_epoch"]) is int and
            0 < receipt["fencing_epoch"] <= lease.epoch, "scene_ir_fencing_identity")
        return document.to_dict(), receipt

    def status(self, run, tenant):
        result = super().status(run, tenant)
        result["scene_ir"] = None
        if result["stages"]["SCENE_IR"] == "SUCCEEDED":
            _, receipt = self.verified_scene_ir(run, tenant)
            result["scene_ir"] = {k: receipt[k] for k in ("output_artifact_id", "output_sha256", "schema_version",
                "document_fingerprint", "element_count", "track_count", "native_validator_count", "single_scene",
                "validation", "compiler_loader_admitted", "requires_review", "accepted", "release_ready",
                "audio_complete", "audio_reconciliation_open")}
        return result
