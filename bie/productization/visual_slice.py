"""Current Director adoption and native Visual execution in the existing durable run."""
from dataclasses import asdict
from contextlib import contextmanager

from bie.director.director_consumers import DirectorConsumers
from bie.director.director_revisions import DirectorRevisionStore
from bie.director.director_inputs import load_director_inputs
from bie.director.narration_visual_sync import sync_visual_intents
from bie.director.sync_contract import build_sync_context
from bie.visual_intelligence.director_handoff_adoption import (
    DirectorHandoff, VisualIntent, TimingCue, adopt)
from bie.visual_intelligence.visual_plan_contract import STAGES as INTERNAL_STAGES
from bie.visual_intelligence.replay_currentness import VersionVector, make_replay_record, assert_current
from bie.infrastructure.orchestrator import StageExecutionResult, StageExecutionFailure
from .contracts import require, ProducerError, digest, canonical
from .director_slice import DirectorProducerService, STAGES as DIRECTOR_STAGES
from .director_storage import native_runtime, import_native_result
from .visual_contract import PROFILE, SCHEMA, POLICY, profile_config, run_identity, refresh_code_identity
from .visual_intents import derive_intents
from .visual_plan import build_current_plan, validate_current_plan

STAGES = DIRECTOR_STAGES + ("VISUAL",)
RECEIPT_FIELDS = frozenset(("schema", "run_id", "stage", "profile", "policy", "attempt",
    "source_sha256", "input_artifact_ids", "input_sha256", "output_artifact_id", "output_sha256",
    "schema_version", "plan_fingerprint", "sync_ref", "current_inputs_id", "internal_record_ids",
    "validation_id", "handoff_id", "replay", "target_sha256", "visual_intent_count", "abstention_count",
    "internal_stage_count", "validation", "animation_input_compatibility", "requires_review", "accepted",
    "release_ready", "visual_executed", "animation_executed", "audio_complete", "evidence_kind",
    "historical_dir_runtime_claimed", "historical_rep_archive_runtime_claimed", "product_accepted",
    "fencing_epoch"))


def animation_compatibility(plan, handoff, context, records, revision):
    """Actual native admission only; it constructs no Animation plan or tracks."""
    from bie.animation_intelligence.vis_ani_adoption import adopt_visual_handoff
    require(handoff.plan_fingerprint == plan.fingerprint and handoff.review_required is True
            and handoff.accepted is False, "visual_handoff_identity_mismatch")
    windows = {r["intent_id"]: next(c for c in context.cues if c.intent_id == r["intent_id"])
               for r in records}
    for timing in handoff.timing:
        record = next((r for r in records if timing.visual_id.startswith(r["intent_id"] + ":")), None)
        require(record is not None, "visual_timing_identity_mismatch")
        cue = windows[record["intent_id"]]
        require(timing.narration_revision == context.narration_revision == revision and
                timing.start_ms == cue.start_ms and timing.end_ms == cue.end_ms,
                "visual_timing_identity_mismatch")
    adopted = adopt_visual_handoff(asdict(handoff), revision, plan.fingerprint)
    require(adopted.accepted is False, "visual_review_boundary")
    return True


def current_context(output, candidate, execution, records, revision):
    """Current native handoff, never relabelled as the historical pinned packet."""
    result = candidate.payload["result"]
    require(result["status"] == "READY_FOR_DOWNSTREAM_REVIEW" if "status" in result else not result["issues"],
            "visual_sync_blocked")
    require(not result["issues"] and candidate.metadata.get("status") == "REVIEW_REQUIRED",
            "visual_sync_blocked")
    by_id = {r["intent_id"]: r for r in records}
    intents, cues = [], []
    require(len(by_id) == len(records), "visual_intent_identity")
    for cue in result["cues"]:
        iid = cue["binding"]["intent_id"]
        require(iid in by_id, "visual_foreign_intent")
        record = by_id[iid]
        intents.append(VisualIntent(iid, cue["kind"], tuple(cue["binding"]["evidence_ids"]),
            tuple(record["reasoning_refs"]), dict(record, director_ref=asdict(output.to_ref()),
                snapshot_fingerprint=execution.snapshot.fingerprint(), scene_id=cue["window"]["scene_id"])))
        cues.append(TimingCue("cue-" + digest(cue), iid, cue["window"]["start_ms"],
                              cue["window"]["end_ms"], revision))
    require({i.intent_id for i in intents} == set(by_id), "visual_intent_coverage")
    source_id = records[0]["source_id"]
    require(all(r["source_id"] == source_id for r in records), "visual_source_mismatch")
    handoff = DirectorHandoff(candidate.artifact_id, revision, source_id, 1, revision,
                             tuple(intents), tuple(cues))
    return adopt(handoff, expected_source_id=source_id, expected_source_revision=1,
                 minimum_revision=revision, expected_token=handoff.currentness_token)


class VisualProducerService(DirectorProducerService):
    stages = STAGES
    profile = PROFILE
    capability = "producer:" + PROFILE
    completion_stage = "VISUAL"
    config_for = staticmethod(profile_config)
    identity_for = staticmethod(run_identity)
    downstream = tuple(s for s in DirectorProducerService.graph_for().stages if s not in STAGES)
    blocked_codes = DirectorProducerService.blocked_codes | frozenset({
        "visual_no_supported_semantics", "visual_sync_blocked", "visual_grammar_unsupported",
        "visual_representation_unsupported", "visual_containment_layout_required",
        "visual_semantic_blocked", "visual_accessibility_blocked"})

    def canonical_config(self, config):
        return profile_config(config["provider"], config["model"],
                              director=config.get("director"), visual=config.get("visual"))

    def verify_terminal_for_ack(self, run, tenant):
        refresh_code_identity()
        # Inherited full status still reopens/revalidates all CAS and native
        # evidence. Only redundant source-code hashing is scoped, never artifacts.
        super().verify_terminal_for_ack(run, tenant)

    @contextmanager
    def publication_guard(self, run, director):
        # The native revision lock is stage-internal, not another run authority.
        # No provider or Visual engine call runs in this short publication lock.
        with native_runtime(self, run, None) as assembly:
            verified = assembly.io.load(director.to_ref())
            with DirectorRevisionStore(assembly.idempotency).guard(verified):
                yield

    def current_inputs(self, run, tenant, *, publish=False, sync_ref=None):
        config = self.configuration(run, tenant)
        output, _ = self.verified_director(run, tenant)
        request, components, _ = self.request(run, tenant)
        with native_runtime(self, run, None) as assembly:
            consumers = DirectorConsumers(assembly.io, DirectorRevisionStore(assembly.idempotency))
            output, execution = consumers._director(output.to_ref())
            inputs = load_director_inputs(assembly.io, request.reasoning_ref, request.pedagogy_ref,
                lesson_id=request.lesson_id, title=request.title, language=request.language, run_id=run)
            typed, records, abstentions = derive_intents(inputs, execution)
            require(typed and records, "visual_no_supported_semantics")
            require(not any(a["status"] in ("BLOCKED", "REVIEW_REQUIRED") for a in abstentions),
                    "visual_unresolved_source_obligation")
            self.fault("after_VISUAL_intent_derivation") if publish else None
            expected = sync_visual_intents(build_sync_context(execution.speech, execution.pauses,
                execution.emphasis, execution.timeline), typed)
            require(not expected.issues, "visual_sync_blocked")
            if publish:
                candidate_ref = consumers.visual(output.to_ref(), typed)
                import_native_result(self, run, assembly.io.catalog, [candidate_ref])
                self.fault("after_VISUAL_sync_candidate")
            else:
                require(sync_ref is not None, "visual_sync_missing")
                candidate_ref = sync_ref
            candidate = consumers.read_current(candidate_ref)
            require(candidate.artifact_type == "director.visual_sync_candidate" and
                canonical(candidate.payload["parameters"]["intents"]) == canonical([asdict(i) for i in typed]) and
                canonical(candidate.payload["result"]) == canonical(asdict(expected)), "visual_sync_mismatch")
            revision = config["config"]["director"]["revision"]
            context = current_context(output, candidate, execution, records, revision)
            # Native objectives are validated by load_director_inputs; additionally
            # prove each real concept/evidence belongs to the original KI graph.
            _, knowledge, _, _, _, _, _ = self.upstream(run, config)
            nodes = knowledge["nodes"]
            for intent in typed:
                require(set(intent.binding.concept_ids) <= nodes.keys(), "visual_foreign_concept")
                require(all(set(intent.binding.evidence_ids) <= set(nodes[c]["anchor_ids"])
                            for c in intent.binding.concept_ids), "visual_concept_evidence_mismatch")
            return context, records, abstentions, candidate, output, components

    def executor(self, config, stage, lease):
        if stage != "VISUAL":
            return super().executor(config, stage, lease)
        def execute(context):
            run = context.run_id
            try:
                director_id, _ = self.stage_ref(run, "DIRECTOR")
                reasoning_id, _ = self.stage_ref(run, "REASONING")
                require(context.input_artifact_refs == [director_id, reasoning_id], "visual_upstream_identity")
                ctx, records, abstentions, candidate, director, components = self.current_inputs(
                    run, config["tenant"], publish=True)
                target = config["config"]["visual"]["target"]
                revision = config["config"]["director"]["revision"]
                plan, handoff, details = build_current_plan(ctx, records, target, run_id=run, revision=revision)
                animation_compatibility(plan, handoff, ctx, records, revision)
                require(tuple(s.stage for s in plan.stages) == INTERNAL_STAGES and plan.current and
                        plan.review_required is True and plan.accepted is False, "visual_plan_contract")
                with self.publication_guard(run, director):
                    parents = context.input_artifact_refs + [candidate.artifact_id]
                    inputs_id = self.put(run, stage, "visual.current_inputs", dict(records=records,
                        abstentions=abstentions, context=asdict(ctx), director_ref=asdict(director.to_ref()),
                        sync_ref=asdict(candidate.to_ref()), target=target, upstream=components["upstream"]), parents)
                    stage_ids = [self.put(run, stage, "visual.stage", asdict(s), parents + [inputs_id])
                                 for s in plan.stages]
                    detail_id = self.put(run, stage, "visual.validation", details, parents + [inputs_id] + stage_ids)
                    handoff_id = self.put(run, stage, "visual.handoff", asdict(handoff), parents + stage_ids)
                    output_id = self.put(run, stage, "visual.plan", plan.to_dict(),
                        parents + [inputs_id, detail_id, handoff_id] + stage_ids)
                    vector = VersionVector(1, revision, SCHEMA, POLICY, digest(target))
                    replay = make_replay_record(run, vector, digest(dict(context=asdict(ctx), records=records,
                        visual=config["config"]["visual"])), plan.fingerprint, parents)
                    receipt = dict(schema="bie.producer.stage-evidence/1", run_id=run, stage=stage,
                        profile=PROFILE, policy=POLICY, attempt=context.attempt,
                        source_sha256=config["source_sha256"], input_artifact_ids=context.input_artifact_refs,
                        input_sha256=[self.record(run, p).blob_digest for p in context.input_artifact_refs],
                        output_artifact_id=output_id, output_sha256=self.record(run, output_id).blob_digest,
                        schema_version=SCHEMA, plan_fingerprint=plan.fingerprint,
                        sync_ref=asdict(candidate.to_ref()), current_inputs_id=inputs_id, internal_record_ids=stage_ids,
                        validation_id=detail_id, handoff_id=handoff_id, replay=asdict(replay),
                        target_sha256=digest(target), visual_intent_count=len(records), abstention_count=len(abstentions),
                        internal_stage_count=8, validation="PASS", animation_input_compatibility=True,
                        requires_review=True, accepted=False, release_ready=False, visual_executed=True,
                        animation_executed=False, audio_complete=False, evidence_kind="TECHNICAL_SOURCE_DERIVED",
                        historical_dir_runtime_claimed=False, historical_rep_archive_runtime_claimed=False,
                        product_accepted=False, fencing_epoch=lease.epoch)
                    safe = self.put(run, stage, "producer.evidence", receipt, parents + [output_id], True)
                    self.write_guard()
                return StageExecutionResult([output_id], [safe])
            except Exception as exc:
                code = exc.code if isinstance(exc, ProducerError) else "visual_execution_failed"
                evidence = self.put(run, stage, "producer.failure", dict(schema="bie.producer.failure/1",
                    code=code, stage=stage, attempt=context.attempt, product_accepted=False), evidence=True)
                raise StageExecutionFailure([code], [evidence], "PROD034") from None
        return execute

    def verified_visual(self, run, tenant):
        config = self.configuration(run, tenant)
        aid, row = self.stage_ref(run, "VISUAL")
        attempt = self.persistence.load_run_state(run)["stages"]["VISUAL"]["attempts"][-1]
        require(len(attempt["evidence_refs"]) == 1, "visual_receipt_mismatch")
        safe = self.record(run, attempt["evidence_refs"][0])
        require(safe.stage_id == "VISUAL" and safe.artifact_type == "producer.evidence" and
                safe.evidence is True and safe.metadata.get("privacy") == "SAFE_EVIDENCE",
                "visual_receipt_mismatch")
        receipt = self.read(run, attempt["evidence_refs"][0])
        require(type(receipt) is dict and set(receipt) == RECEIPT_FIELDS and
                receipt.get("schema") == "bie.producer.stage-evidence/1" and
                receipt.get("run_id") == run and receipt.get("stage") == "VISUAL" and
                receipt.get("profile") == PROFILE and receipt.get("policy") == POLICY and
                receipt.get("schema_version") == SCHEMA and receipt.get("source_sha256") == config["source_sha256"] and
                receipt.get("input_artifact_ids") == attempt["input_artifact_refs"] and
                receipt.get("validation") == "PASS" and receipt.get("requires_review") is True and
                receipt.get("accepted") is False and receipt.get("release_ready") is False and
                receipt.get("internal_stage_count") == 8 and receipt.get("visual_executed") is True and
                receipt.get("animation_executed") is False and receipt.get("audio_complete") is False and
                receipt.get("animation_input_compatibility") is True and
                receipt.get("evidence_kind") == "TECHNICAL_SOURCE_DERIVED" and
                receipt.get("historical_dir_runtime_claimed") is False and
                receipt.get("historical_rep_archive_runtime_claimed") is False and
                receipt.get("product_accepted") is False and
                type(receipt.get("fencing_epoch")) is int and receipt["fencing_epoch"] > 0 and
                type(receipt.get("attempt")) is int and type(receipt.get("internal_stage_count")) is int,
                "visual_receipt_mismatch")
        saved_lease = self.leases.get(self.task_id(run, "VISUAL", attempt["attempt"]))
        require(saved_lease.fingerprint == config["fingerprint"] and
                receipt["fencing_epoch"] <= saved_lease.epoch, "visual_receipt_mismatch")
        from bie.director.director_artifacts import reference
        ctx, records, abstentions, candidate, director, components = self.current_inputs(
            run, tenant, sync_ref=reference(receipt["sync_ref"]))
        require(type(receipt.get("visual_intent_count")) is int and receipt["visual_intent_count"] == len(records) and
                type(receipt.get("abstention_count")) is int and receipt["abstention_count"] == len(abstentions),
                "visual_receipt_mismatch")
        settings = config["config"]["visual"]
        plan_dict = self.read(run, aid)
        handoff = self.read(run, receipt["handoff_id"])
        details = self.read(run, receipt["validation_id"])
        verified_plan, verified_handoff, _ = validate_current_plan(ctx, records, settings["target"], run_id=run,
            revision=config["config"]["director"]["revision"], plan_dict=plan_dict,
            handoff_dict=handoff, receipts=details)
        animation_compatibility(verified_plan, verified_handoff, ctx, records,
                                config["config"]["director"]["revision"])
        parents = attempt["input_artifact_refs"] + [candidate.artifact_id]
        expected_inputs = dict(records=records, abstentions=abstentions, context=asdict(ctx),
            director_ref=asdict(director.to_ref()), sync_ref=asdict(candidate.to_ref()),
            target=settings["target"], upstream=components["upstream"])
        require(canonical(self.read(run, receipt["current_inputs_id"])) == canonical(expected_inputs),
                "visual_intent_mismatch")
        require(receipt["output_artifact_id"] == aid and receipt["output_sha256"] == row.blob_digest and
            receipt["plan_fingerprint"] == plan_dict["fingerprint"] and
            receipt["target_sha256"] == digest(settings["target"]) and receipt["attempt"] == attempt["attempt"] and
            receipt["input_sha256"] == [self.record(run, p).blob_digest for p in attempt["input_artifact_refs"]],
            "visual_receipt_mismatch")
        require(len(receipt["internal_record_ids"]) == 8, "visual_internal_stage_missing")
        for ref, stage in zip(receipt["internal_record_ids"], plan_dict["stages"]):
            record = self.record(run, ref)
            require(record.stage_id == "VISUAL" and record.artifact_type == "visual.stage" and
                    canonical(self.read(run, ref)) == canonical(stage), "visual_internal_stage_mismatch")
        expected_replay = make_replay_record(run, VersionVector(1,
            config["config"]["director"]["revision"], SCHEMA, POLICY, digest(settings["target"])),
            digest(dict(context=asdict(ctx), records=records, visual=settings)), plan_dict["fingerprint"], parents)
        assert_current(expected_replay, expected_replay.version_vector, expected_replay.input_fingerprint, parents)
        require(canonical(receipt["replay"]) == canonical(asdict(expected_replay)), "visual_stale_plan")
        require(set(parents + [receipt["current_inputs_id"], receipt["handoff_id"],
            receipt["validation_id"]] + receipt["internal_record_ids"]) == set(row.parent_artifact_ids),
            "visual_upstream_identity")
        return plan_dict, receipt

    def status(self, run, tenant):
        result = super().status(run, tenant)
        result["visual"] = None
        if result["stages"]["VISUAL"] == "SUCCEEDED":
            _, receipt = self.verified_visual(run, tenant)
            result["visual"] = {k: receipt[k] for k in ("output_artifact_id", "output_sha256",
                "schema_version", "plan_fingerprint", "visual_intent_count", "abstention_count",
                "internal_stage_count", "validation", "animation_input_compatibility", "requires_review",
                "accepted", "release_ready")}
        return result
