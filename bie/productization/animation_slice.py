"""Task035 executes native Animation in the existing durable producer run."""
from dataclasses import asdict

from bie.director.director_artifacts import reference
from bie.director.director_consumers import DirectorConsumers
from bie.director.director_revisions import DirectorRevisionStore
from bie.director.director_inputs import load_director_inputs
from bie.director.recovery_codec import decode
from bie.director.narration_visual_sync import VisualIntent, sync_visual_intents
from bie.director.narration_animation_sync import sync_animation_intents
from bie.director.sync_contract import build_sync_context
from bie.animation_intelligence.ani_orchestrator import STAGES as INTERNAL_STAGES
from bie.animation_intelligence.ani_replay_currentness import VersionVector, make_replay_record, assert_current
from bie.infrastructure.orchestrator import StageExecutionResult, StageExecutionFailure
from .contracts import require, ProducerError, canonical, digest
from .visual_slice import VisualProducerService, STAGES as VISUAL_STAGES
from .director_storage import native_runtime, import_native_result
from .animation_contract import PROFILE, SCHEMA, POLICY, profile_config, run_identity, refresh_code_identity
from .animation_intents import derive_animation_intents
from .animation_plan import build_current_animation

STAGES = VISUAL_STAGES + ("ANIMATION",)
RECEIPT_FIELDS = frozenset(("schema", "run_id", "stage", "profile", "policy", "attempt",
    "source_sha256", "input_artifact_ids", "input_sha256", "output_artifact_id", "output_sha256",
    "schema_version", "plan_fingerprint", "sync_ref", "current_inputs_id", "validation_id", "handoff_id",
    "visual_handoff_id", "visual_handoff_sha256", "visual_plan_fingerprint", "visual_revision",
    "narration_revision", "target_sha256", "replay", "internal_stage_count", "track_count", "validation",
    "sceneir_handoff_ready", "requires_review", "accepted", "release_ready", "animation_executed",
    "scene_ir_executed", "audio_complete", "audio_reconciliation_open", "evidence_kind",
    "product_accepted", "fencing_epoch"))


def check_sync(result):
    require(not any(issue.code == "AUDIO_REPLAN_REQUIRED" for issue in result.issues),
            "animation_audio_replan_required")
    require(not result.issues, "animation_sync_blocked")


class AnimationProducerService(VisualProducerService):
    stages = STAGES
    profile = PROFILE
    capability = "producer:" + PROFILE
    completion_stage = "ANIMATION"
    config_for = staticmethod(profile_config)
    identity_for = staticmethod(run_identity)
    downstream = tuple(s for s in VisualProducerService.graph_for().stages if s not in STAGES)
    blocked_codes = VisualProducerService.blocked_codes | frozenset({
        "animation_audio_replan_required", "animation_sync_blocked", "animation_semantics_required",
        "animation_native_blocked", "animation_qa_blocked", "animation_duration_blocked",
        "animation_accessibility_blocked", "animation_performance_blocked", "animation_timeline_unsat"})

    def canonical_config(self, config):
        return profile_config(config["provider"], config["model"], director=config.get("director"),
                              visual=config.get("visual"), animation=config.get("animation"))

    def verify_terminal_for_ack(self, run, tenant):
        refresh_code_identity()
        super().verify_terminal_for_ack(run, tenant)

    def require_parents(self, run, artifact_id, expected):
        record = self.record(run, artifact_id)
        require(set(record.parent_artifact_ids) == set(expected), "animation_parent_identity")

    def animation_inputs(self, run, tenant, *, publish=False, sync_ref=None):
        config = self.configuration(run, tenant)
        visual_plan, visual_receipt = self.verified_visual(run, tenant)
        visual_globals = [self.stage_ref(run, s)[0] for s in ("DIRECTOR", "REASONING")]
        saved_visual = self.persistence.load_run_state(run)["stages"]["VISUAL"]["attempts"][-1]
        require(saved_visual["input_artifact_refs"] == visual_globals, "animation_visual_upstream_identity")
        visual_parents = visual_globals + [visual_receipt["sync_ref"]["artifact_id"]]
        stage_ids = visual_receipt["internal_record_ids"]
        self.require_parents(run, visual_receipt["current_inputs_id"], visual_parents)
        for ref in stage_ids:
            self.require_parents(run, ref, visual_parents + [visual_receipt["current_inputs_id"]])
        self.require_parents(run, visual_receipt["validation_id"],
            visual_parents + [visual_receipt["current_inputs_id"]] + stage_ids)
        self.require_parents(run, visual_receipt["handoff_id"], visual_parents + stage_ids)
        self.require_parents(run, saved_visual["evidence_refs"][0],
            visual_parents + [visual_receipt["output_artifact_id"]])
        handoff = self.read(run, visual_receipt["handoff_id"])
        current_inputs = self.read(run, visual_receipt["current_inputs_id"])
        validation = self.read(run, visual_receipt["validation_id"])
        for ref, kind in ((visual_receipt["handoff_id"], "visual.handoff"),
                          (visual_receipt["current_inputs_id"], "visual.current_inputs"),
                          (visual_receipt["validation_id"], "visual.validation")):
            record = self.record(run, ref)
            require(record.stage_id == "VISUAL" and record.artifact_type == kind and not record.evidence,
                    "animation_visual_support_identity")
        request, _, _ = self.request(run, tenant)
        director_id, _ = self.stage_ref(run, "DIRECTOR")
        with native_runtime(self, run, None) as assembly:
            consumers = DirectorConsumers(assembly.io, DirectorRevisionStore(assembly.idempotency))
            director, execution = consumers._director(assembly.io.load(director_id).to_ref())
            visual_sync = consumers.read_current(reference(visual_receipt["sync_ref"]))
            require(visual_sync.artifact_type == "director.visual_sync_candidate" and
                    visual_sync.payload["director_ref"] == asdict(director.to_ref()),
                    "animation_visual_sync_identity")
            context = build_sync_context(execution.speech, execution.pauses, execution.emphasis, execution.timeline)
            native_visuals = sync_visual_intents(context,
                decode(tuple[VisualIntent, ...], visual_sync.payload["parameters"]["intents"]))
            check_sync(native_visuals)
            require(canonical(asdict(native_visuals)) == canonical(visual_sync.payload["result"]),
                    "animation_visual_sync_identity")
            inputs = load_director_inputs(assembly.io, request.reasoning_ref, request.pedagogy_ref,
                lesson_id=request.lesson_id, title=request.title, language=request.language, run_id=run)
            if publish:
                self.fault("after_ANIMATION_visual_verified")
            typed, rows = derive_animation_intents(inputs, execution, visual_sync,
                current_inputs["records"], visual_plan, handoff, validation,
                visual_revision=config["config"]["director"]["revision"],
                target_profile=config["config"]["visual"]["target"]["profile_id"])
            require(typed and rows, "animation_semantics_required")
            if publish:
                self.fault("after_ANIMATION_intent_derivation")
            expected = sync_animation_intents(context, native_visuals, typed)
            check_sync(expected)
            if publish:
                candidate_ref = consumers.animation(director.to_ref(), visual_sync.to_ref(), typed)
                import_native_result(self, run, assembly.io.catalog, [candidate_ref])
                self.fault("after_ANIMATION_sync_candidate")
            else:
                require(sync_ref is not None, "animation_sync_missing")
                candidate_ref = sync_ref
            candidate = consumers.read_current(candidate_ref)
            require(candidate.artifact_type == "director.animation_sync_candidate" and
                    candidate.payload["director_ref"] == asdict(director.to_ref()) and
                    visual_sync.to_ref() in candidate.parent_refs and
                    canonical(candidate.payload["parameters"]["intents"]) == canonical([asdict(i) for i in typed]) and
                    canonical(candidate.payload["result"]) == canonical(asdict(expected)),
                    "animation_sync_mismatch")
            return dict(visual_plan=visual_plan, visual_receipt=visual_receipt, handoff=handoff,
                current_inputs=current_inputs, rows=rows, typed=typed, candidate=candidate, director=director)

    def _private_inputs(self, bundle, settings):
        return dict(rows=bundle["rows"], settings=settings,
            director_ref=asdict(bundle["director"].to_ref()), sync_ref=asdict(bundle["candidate"].to_ref()),
            visual_plan_id=bundle["visual_receipt"]["output_artifact_id"],
            visual_plan_sha256=bundle["visual_receipt"]["output_sha256"],
            visual_handoff_id=bundle["visual_receipt"]["handoff_id"],
            visual_inputs_id=bundle["visual_receipt"]["current_inputs_id"],
            visual_validation_id=bundle["visual_receipt"]["validation_id"])

    def _replay(self, run, config, bundle, plan, parents):
        settings = config["config"]["animation"]
        vector = VersionVector(plan.visual_revision, plan.narration_revision,
            settings["policy_revision"], settings["domain_registry_version"], plan.target_profile)
        identity = digest(self._private_inputs(bundle, settings))
        replay = make_replay_record(run, vector, identity, plan.plan_fingerprint, parents)
        assert_current(replay, vector, identity, parents)
        return replay

    def executor(self, config, stage, lease):
        if stage != "ANIMATION":
            return super().executor(config, stage, lease)
        def execute(context):
            run = context.run_id
            try:
                visual_id, _ = self.stage_ref(run, "VISUAL")
                director_id, _ = self.stage_ref(run, "DIRECTOR")
                require(context.input_artifact_refs == [visual_id, director_id], "animation_upstream_identity")
                bundle = self.animation_inputs(run, config["tenant"], publish=True)
                settings = config["config"]["animation"]
                plan, handoff, details = build_current_animation(bundle["rows"], settings,
                    run_id=run, handoff=bundle["handoff"], fault=self.fault)
                require(tuple(r["stage"] for r in details["stages"]) == INTERNAL_STAGES and
                        plan.accepted is False and handoff.accepted is False and handoff.review_required is True,
                        "animation_plan_contract")
                with self.publication_guard(run, bundle["director"]):
                    parents = context.input_artifact_refs + [bundle["candidate"].artifact_id,
                        bundle["visual_receipt"]["handoff_id"], bundle["visual_receipt"]["current_inputs_id"],
                        bundle["visual_receipt"]["validation_id"]]
                    inputs_id = self.put(run, stage, "animation.current_inputs", self._private_inputs(bundle, settings), parents)
                    validation_id = self.put(run, stage, "animation.validation", details, parents + [inputs_id])
                    handoff_id = self.put(run, stage, "animation.sceneir_handoff", asdict(handoff), parents + [inputs_id, validation_id])
                    output_id = self.put(run, stage, "animation.plan", asdict(plan),
                        parents + [inputs_id, validation_id, handoff_id])
                    replay = self._replay(run, config, bundle, plan, parents)
                    receipt = dict(schema="bie.producer.stage-evidence/1", run_id=run, stage=stage,
                        profile=PROFILE, policy=POLICY, attempt=context.attempt, source_sha256=config["source_sha256"],
                        input_artifact_ids=context.input_artifact_refs,
                        input_sha256=[self.record(run, p).blob_digest for p in context.input_artifact_refs],
                        output_artifact_id=output_id, output_sha256=self.record(run, output_id).blob_digest,
                        schema_version=SCHEMA, plan_fingerprint=plan.plan_fingerprint,
                        sync_ref=asdict(bundle["candidate"].to_ref()), current_inputs_id=inputs_id,
                        validation_id=validation_id, handoff_id=handoff_id,
                        visual_handoff_id=bundle["visual_receipt"]["handoff_id"],
                        visual_handoff_sha256=self.record(run, bundle["visual_receipt"]["handoff_id"]).blob_digest,
                        visual_plan_fingerprint=plan.visual_plan_fingerprint, visual_revision=plan.visual_revision,
                        narration_revision=plan.narration_revision, target_sha256=digest(config["config"]["visual"]["target"]),
                        replay=asdict(replay), internal_stage_count=9, track_count=len(plan.tracks), validation="PASS",
                        sceneir_handoff_ready=True, requires_review=True, accepted=False, release_ready=False,
                        animation_executed=True, scene_ir_executed=False, audio_complete=False,
                        audio_reconciliation_open=True, evidence_kind="TECHNICAL_SOURCE_DERIVED",
                        product_accepted=False, fencing_epoch=lease.epoch)
                    safe = self.put(run, stage, "producer.evidence", receipt, parents + [output_id], True)
                    self.write_guard()
                    self.fault("before_ANIMATION_terminal")
                return StageExecutionResult([output_id], [safe])
            except Exception as exc:
                code = exc.code if isinstance(exc, ProducerError) else "animation_execution_failed"
                safe = self.put(run, stage, "producer.failure", dict(schema="bie.producer.failure/1",
                    code=code, stage=stage, attempt=context.attempt, product_accepted=False), evidence=True)
                raise StageExecutionFailure([code], [safe], "PROD035") from None
        return execute

    def verified_animation(self, run, tenant):
        config = self.configuration(run, tenant)
        aid, row = self.stage_ref(run, "ANIMATION")
        attempt = self.persistence.load_run_state(run)["stages"]["ANIMATION"]["attempts"][-1]
        require(attempt["input_artifact_refs"] == [self.stage_ref(run, s)[0] for s in ("VISUAL", "DIRECTOR")],
                "animation_upstream_identity")
        require(len(attempt["evidence_refs"]) == 1, "animation_receipt_mismatch")
        safe = self.record(run, attempt["evidence_refs"][0])
        require(safe.stage_id == "ANIMATION" and safe.artifact_type == "producer.evidence" and safe.evidence is True
                and safe.metadata.get("privacy") == "SAFE_EVIDENCE", "animation_receipt_mismatch")
        receipt = self.read(run, safe.artifact_id)
        require(type(receipt) is dict and set(receipt) == RECEIPT_FIELDS, "animation_receipt_mismatch")
        bundle = self.animation_inputs(run, tenant, sync_ref=reference(receipt["sync_ref"]))
        settings = config["config"]["animation"]
        plan, handoff, details = build_current_animation(bundle["rows"], settings, run_id=run, handoff=bundle["handoff"])
        raw = self.read(run, aid)
        require(raw.get("accepted") is False and raw.get("plan_fingerprint") == plan.plan_fingerprint and
                canonical(raw) == canonical(asdict(plan)), "animation_plan_tampered")
        parents = attempt["input_artifact_refs"] + [bundle["candidate"].artifact_id,
            bundle["visual_receipt"]["handoff_id"], bundle["visual_receipt"]["current_inputs_id"],
            bundle["visual_receipt"]["validation_id"]]
        self.require_parents(run, receipt["current_inputs_id"], parents)
        self.require_parents(run, receipt["validation_id"], parents + [receipt["current_inputs_id"]])
        self.require_parents(run, receipt["handoff_id"],
            parents + [receipt["current_inputs_id"], receipt["validation_id"]])
        self.require_parents(run, safe.artifact_id, parents + [aid])
        for ref, kind, value in ((receipt["current_inputs_id"], "animation.current_inputs", self._private_inputs(bundle, settings)),
                (receipt["validation_id"], "animation.validation", details),
                (receipt["handoff_id"], "animation.sceneir_handoff", asdict(handoff))):
            artifact = self.record(run, ref)
            require(artifact.stage_id == "ANIMATION" and artifact.artifact_type == kind and not artifact.evidence
                    and canonical(self.read(run, ref)) == canonical(value), "animation_support_tampered")
        expected = dict(schema="bie.producer.stage-evidence/1", run_id=run, stage="ANIMATION", profile=PROFILE,
            policy=POLICY, attempt=attempt["attempt"], source_sha256=config["source_sha256"],
            input_artifact_ids=attempt["input_artifact_refs"],
            input_sha256=[self.record(run, p).blob_digest for p in attempt["input_artifact_refs"]],
            output_artifact_id=aid, output_sha256=row.blob_digest, schema_version=SCHEMA,
            plan_fingerprint=plan.plan_fingerprint, sync_ref=asdict(bundle["candidate"].to_ref()),
            current_inputs_id=receipt["current_inputs_id"], validation_id=receipt["validation_id"], handoff_id=receipt["handoff_id"],
            visual_handoff_id=bundle["visual_receipt"]["handoff_id"],
            visual_handoff_sha256=self.record(run, bundle["visual_receipt"]["handoff_id"]).blob_digest,
            visual_plan_fingerprint=plan.visual_plan_fingerprint, visual_revision=plan.visual_revision,
            narration_revision=plan.narration_revision, target_sha256=digest(config["config"]["visual"]["target"]),
            replay=asdict(self._replay(run, config, bundle, plan, parents)), internal_stage_count=9,
            track_count=len(plan.tracks), validation="PASS", sceneir_handoff_ready=True, requires_review=True,
            accepted=False, release_ready=False, animation_executed=True, scene_ir_executed=False,
            audio_complete=False, audio_reconciliation_open=True, evidence_kind="TECHNICAL_SOURCE_DERIVED",
            product_accepted=False, fencing_epoch=receipt["fencing_epoch"])
        require(canonical(receipt) == canonical(expected), "animation_receipt_mismatch")
        lease = self.leases.get(self.task_id(run, "ANIMATION", attempt["attempt"]))
        require(lease.fingerprint == config["fingerprint"] and type(receipt["fencing_epoch"]) is int and
                0 < receipt["fencing_epoch"] <= lease.epoch, "animation_receipt_mismatch")
        require(set(parents + [receipt["current_inputs_id"], receipt["validation_id"], receipt["handoff_id"]]) ==
                set(row.parent_artifact_ids), "animation_upstream_identity")
        return raw, receipt

    def status(self, run, tenant):
        result = super().status(run, tenant)
        result["animation"] = None
        if result["stages"]["ANIMATION"] == "SUCCEEDED":
            _, receipt = self.verified_animation(run, tenant)
            result["animation"] = {k: receipt[k] for k in ("output_artifact_id", "output_sha256", "schema_version",
                "plan_fingerprint", "track_count", "internal_stage_count", "validation", "sceneir_handoff_ready",
                "requires_review", "accepted", "release_ready", "audio_complete", "audio_reconciliation_open")}
        return result
