"""Eleven-stage delegation using existing durable stores and fenced publication."""
from dataclasses import asdict
from contextlib import contextmanager
from contextvars import ContextVar
from bie.infrastructure.orchestrator import EnterpriseOrchestrator, StageExecutionResult, StageExecutionFailure
from bie.infrastructure.artifact_store import BlobRef
from bie.scene_ir.replay_currentness import DSLVersionVector, make_replay_record, evaluate_currentness, require_current
from bie.scene_ir.unified_scene_ir_codec import encode_scene_ir
from bie.compiler.scene_ir_loader import load_scene_ir_payload
from .animation_slice import AnimationProducerService, STAGES as ANIMATION_STAGES
from .pedagogy_slice import PedagogyProducerService
from .contracts import require, ProducerError, canonical, digest, sha
from .scene_ir_contract import PROFILE, POLICY, SCHEMA, profile_config, run_identity, refresh_code_identity, strict_document
from .scene_ir_plan import build_current_scene

STAGES = ANIMATION_STAGES + ("SCENE_IR",)
INPUT_STAGES = ("VISUAL", "ANIMATION", "DIRECTOR")
_ANIMATION_INPUT_CAPTURE = ContextVar("task036_verified_animation_input_capture", default=None)
_MOTION_INPUT_COMPOSITION = ContextVar("task036_current_motion_input_composition", default=None)
_DIRECTOR_STATUS_CAPTURE = ContextVar("task036_fresh_exit_director_status", default=None)
_INCOMPLETE_STATUS_CAPTURE = ContextVar("task036_fresh_animation_status", default=None)
STATUS_COMPOSITION_POLICY = "fresh-animation-complete-scene-incomplete-status/1"
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

    def animation_inputs(self, run, tenant, *, publish=False, sync_ref=None):
        capture = _ANIMATION_INPUT_CAPTURE.get()
        if capture is not None:
            require(capture["service"] is self and capture["run"] == run and capture["tenant"] == tenant
                and publish is False and sync_ref is not None, "scene_ir_animation_capture_scope")
        bundle = super().animation_inputs(run, tenant, publish=publish, sync_ref=sync_ref)
        if capture is not None:
            capture["bundles"].append(bundle)
        return bundle

    def verified_director(self, run, tenant):
        status_capture = _INCOMPLETE_STATUS_CAPTURE.get()
        if status_capture is not None:
            animation_capture = _ANIMATION_INPUT_CAPTURE.get()
            valid = (status_capture["service"] is self and status_capture["run"] == run and
                status_capture["tenant"] == tenant and status_capture["delegating"] is True and
                not status_capture["invalid"] and status_capture["proof_attempts"] == 1 and
                animation_capture is not None and animation_capture is status_capture["animation_capture"] and
                animation_capture["service"] is self and animation_capture["run"] == run and
                animation_capture["tenant"] == tenant and _DIRECTOR_STATUS_CAPTURE.get() is None and
                _MOTION_INPUT_COMPOSITION.get() is None and status_capture["director_attempts"] == 0)
            if not valid:
                status_capture["invalid"] = True
            require(valid, "scene_ir_animation_status_scope")
            status_capture["director_attempts"] += 1
            try:
                value = super().verified_director(run, tenant)
            except BaseException:
                status_capture["invalid"] = True
                raise
            status_capture["director_value"] = value
            return value  # The exact native return, not a sidecar receipt.
        capture = _DIRECTOR_STATUS_CAPTURE.get()
        if capture is None:
            return super().verified_director(run, tenant)
        composition = _MOTION_INPUT_COMPOSITION.get()
        valid = (capture["service"] is self and capture["run"] == run and capture["tenant"] == tenant
            and composition is not None and composition["service"] is self and
            composition["run"] == run and composition["tenant"] == tenant and
            composition["phase"] in ("ENTRY", "EXIT") and composition["delegating"] is True
            and not composition["invalid"] and not capture["invalid"])
        if not valid:
            capture["invalid"] = True
        require(valid, "scene_ir_director_status_scope")
        exiting = composition["phase"] == "EXIT"
        counter = "attempts" if exiting else "entry_attempts"
        if capture[counter] != 0:
            capture["invalid"] = True
        require(not capture["invalid"], "scene_ir_director_status_cardinality")
        capture[counter] += 1  # A caught failure cannot retry this proof.
        try:
            value = super().verified_director(run, tenant)
        except BaseException:
            capture["invalid"] = True
            raise  # Preserve the exact native rejection, including BaseException.
        if exiting:
            capture["value"] = value
        return value  # Exact unchanged native return, never a cached authority.

    def _completed_status_bundle(self, run, tenant):
        """Project only the exact Director proof inside this fresh M1 EXIT.

        Both native ENTRY/EXIT checks still execute, and final Scene persisted
        bytes, dependency equality, replay, receipt and lease checks complete
        before this result is usable. No proof is retained by the service or
        reused across status, ACK, recovery, publication or revision boundaries.
        """
        status_capture = _INCOMPLETE_STATUS_CAPTURE.get()
        if status_capture is not None:
            status_capture["invalid"] = True
        require(status_capture is None, "scene_ir_director_status_nested")
        prior = _DIRECTOR_STATUS_CAPTURE.get()
        if prior is not None:
            prior["invalid"] = True
        require(prior is None, "scene_ir_director_status_nested")
        composition = _MOTION_INPUT_COMPOSITION.get()
        if composition is not None:
            composition["invalid"] = True
        require(composition is None, "scene_ir_director_status_nested")
        capture = dict(service=self, run=run, tenant=tenant, entry_attempts=0, attempts=0, invalid=False, value=None)
        token = _DIRECTOR_STATUS_CAPTURE.set(capture)
        try:
            verified = self._verified_scene_bundle(run, tenant)
            require(capture["entry_attempts"] == capture["attempts"] == 1 and
                capture["value"] is not None and not capture["invalid"],
                "scene_ir_director_status_cardinality")
            output, director_receipt = capture["value"]
            require(output.to_ref() == verified[2]["director"].to_ref(), "scene_ir_director_status_identity")
            return verified, director_receipt
        finally:
            _DIRECTOR_STATUS_CAPTURE.reset(token)

    def _incomplete_status_bundle(self, run, tenant):
        """One fresh native Animation proof, with its actual Director return.

        Only a status operation may own this scope. No proof survives a call or
        crosses ACK/publication; completed Scene IR still uses native ENTRY/EXIT.
        """
        scopes = (_INCOMPLETE_STATUS_CAPTURE.get(), _DIRECTOR_STATUS_CAPTURE.get(),
            _MOTION_INPUT_COMPOSITION.get(), _ANIMATION_INPUT_CAPTURE.get())
        for prior in scopes:
            if prior is not None:
                prior["invalid"] = True
        require(all(prior is None for prior in scopes), "scene_ir_animation_status_nested")
        capture = dict(service=self, run=run, tenant=tenant, delegating=True, invalid=False,
            proof_attempts=0, director_attempts=0, director_value=None, animation_capture=None)
        token = _INCOMPLETE_STATUS_CAPTURE.set(capture)
        try:
            verified = self.verified_animation_with_inputs(run, tenant)
            capture["delegating"] = False
            require(not capture["invalid"] and capture["proof_attempts"] == 1 and
                capture["director_attempts"] == 1 and capture["director_value"] is not None,
                "scene_ir_animation_status_cardinality")
            output, director_receipt = capture["director_value"]
            require(output.to_ref() == verified[2]["director"].to_ref(),
                "scene_ir_animation_status_identity")
            return verified, director_receipt
        finally:
            _INCOMPLETE_STATUS_CAPTURE.reset(token)

    def verified_animation_with_inputs(self, run, tenant):
        """Return the very bundle consumed by one fresh native verification.

        Native Task035 verification still executes unchanged, including every
        currentness, receipt, private artifact, parent, replay and fencing check.
        Its already-verified input rows need not be reconstructed a second time
        inside this same Scene IR build. Nothing survives the context scope;
        no cross-call, ACK, publication, revision or authorization cache exists.
        """
        composition = _MOTION_INPUT_COMPOSITION.get()
        if composition is not None:
            valid = (composition["service"] is self and composition["run"] == run and
                composition["tenant"] == tenant and composition["phase"] in ("ENTRY", "EXIT") and
                composition["delegating"] is True and _ANIMATION_INPUT_CAPTURE.get() is None and
                not composition["invalid"])
            if not valid:
                composition["invalid"] = True
            require(valid, "scene_ir_motion_composition_scope")
        status_capture = _INCOMPLETE_STATUS_CAPTURE.get()
        if status_capture is not None:
            valid = (status_capture["service"] is self and status_capture["run"] == run and
                status_capture["tenant"] == tenant and status_capture["delegating"] is True and
                not status_capture["invalid"] and status_capture["proof_attempts"] == 0 and
                composition is None and _DIRECTOR_STATUS_CAPTURE.get() is None and
                _ANIMATION_INPUT_CAPTURE.get() is None)
            if not valid:
                status_capture["invalid"] = True
            require(valid, "scene_ir_animation_status_scope")
            status_capture["proof_attempts"] += 1
        capture = dict(service=self, run=run, tenant=tenant, bundles=[])
        if status_capture is not None:
            status_capture["animation_capture"] = capture
        token = _ANIMATION_INPUT_CAPTURE.set(capture)
        try:
            plan, receipt = super().verified_animation(run, tenant)
            require(len(capture["bundles"]) == 1, "scene_ir_animation_capture_cardinality")
            return plan, receipt, capture["bundles"][0]
        except BaseException:
            if status_capture is not None:
                status_capture["invalid"] = True
            raise
        finally:
            _ANIMATION_INPUT_CAPTURE.reset(token)

    def verified_animation(self, run, tenant):
        composition = _MOTION_INPUT_COMPOSITION.get()
        if composition is None:
            return super().verified_animation(run, tenant)
        phase = composition["phase"]
        expected = 0 if phase == "ENTRY" else 1 if phase == "EXIT" else None
        valid = (composition["service"] is self and composition["run"] == run and
            composition["tenant"] == tenant and expected is not None and
            composition["attempts"] == expected and not composition["invalid"])
        if not valid:
            composition["invalid"] = True
        require(valid, "scene_ir_motion_composition_scope")
        # Count the attempt BEFORE delegation. A caught native/derivation failure
        # cannot retry or substitute a cached proof within this operation.
        composition["attempts"] += 1
        composition["delegating"] = True
        try:
            plan, receipt, bundle = self.verified_animation_with_inputs(run, tenant)
        finally:
            composition["delegating"] = False
        if phase == "ENTRY":
            prepared, elements = composition["derive"](plan, receipt, bundle)
            require(type(prepared) is dict and type(elements) is list and elements,
                "scene_ir_motion_composition_catalog")
            composition["catalog"].extend(elements)
            composition["prepared"] = prepared
        # Both ENTRY and EXIT executed the unchanged native super() verification.
        # No receipt, authority, or native result is cached for the EXIT call.
        return plan, receipt

    @contextmanager
    def current_scene_motion_admission(self, run, tenant, derive):
        """Populate M1's owned catalog from its ACTUAL fresh entry verification.

        The canonical M1 snapshot/lowering/exit checks are unchanged. Only the
        separate preparatory verification is eliminated. No state survives the
        scope; publication, ACK, status and replay each reopen current authority.
        """
        from bie.compiler.producer_motion_admission import current_motion_admission
        status_capture = _INCOMPLETE_STATUS_CAPTURE.get()
        if status_capture is not None:
            status_capture["invalid"] = True
        require(status_capture is None, "scene_ir_motion_composition_nested")
        prior = _MOTION_INPUT_COMPOSITION.get()
        if prior is not None:
            prior["invalid"] = True
        require(prior is None and _ANIMATION_INPUT_CAPTURE.get() is None,
            "scene_ir_motion_composition_nested")
        require(callable(derive), "scene_ir_motion_composition_callback")
        composition = dict(service=self, run=run, tenant=tenant, phase="ENTRY", attempts=0,
            invalid=False, delegating=False, catalog=[], prepared=None, derive=derive)
        marker = _MOTION_INPUT_COMPOSITION.set(composition)
        try:
            with current_motion_admission(self, run, tenant, composition["catalog"]) as bound:
                require(composition["attempts"] == 1 and composition["prepared"] is not None and
                    not composition["invalid"], "scene_ir_motion_composition_entry")
                composition["phase"] = "BODY"
                yield bound, composition["prepared"]
                require(not composition["invalid"], "scene_ir_motion_composition_scope")
                composition["phase"] = "EXIT"
            require(composition["attempts"] == 2 and not composition["invalid"],
                "scene_ir_motion_composition_exit")
        finally:
            _MOTION_INPUT_COMPOSITION.reset(marker)

    def require_parents(self, run, artifact_id, expected):
        actual = self.record(run, artifact_id).parent_artifact_ids
        require(len(actual) == len(set(actual)) and set(actual) == set(expected), "scene_ir_parent_identity")

    def verify_terminal_for_ack(self, run, tenant):
        refresh_code_identity()
        # The inherited Math ACK hook dispatches self.status: completed Scene
        # IR status already performs one fresh full bundle validation. Preserve
        # the complete refresh/authority chain, not a second identical rebuild.
        super().verify_terminal_for_ack(run, tenant)

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
                motion=private["motion_admission_id"], scope=private["scope"],
                input_composition=private["input_composition_policy"])), digest([]))
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

    def _verified_scene_bundle(self, run, tenant):
        """One fresh complete validation, with its authenticated upstream rows.

        This is not a cache or a receipt-only fast path. The same native rebuild,
        currentness, exact parents, persisted loader, receipt and fencing checks
        execute on every call. Its upstream receipts were reopened by that build.
        """
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
        return document.to_dict(), receipt, bundle, animation_receipt

    def verified_scene_ir(self, run, tenant):
        document, receipt, _, _ = self._verified_scene_bundle(run, tenant)
        return document, receipt

    def status(self, run, tenant):
        prior = _INCOMPLETE_STATUS_CAPTURE.get()
        if prior is not None:
            prior['invalid'] = True
        require(prior is None, "scene_ir_animation_status_nested")
        # A completed Scene IR rebuild already verifies current Visual and
        # Animation. Running their inherited status rebuilds first repeats that
        # work without adding a different admission check. Keep all lower-stage
        # status checks and the identical safe projections; never cache results
        # across calls, publication, recovery, authorization or revisions.
        saved = self.persistence.load_run_state(run)
        complete = saved['stages']['SCENE_IR']['attempts'][-1]['state'] == 'SUCCEEDED'
        animation_complete = not complete and saved['stages']['ANIMATION']['attempts'][-1]['state'] == 'SUCCEEDED'
        composing_animation = animation_complete and not complete
        # This immutable operation-local comparison includes all attempts, refs
        # and evidence of the selected stages. It is not a stored authority/cache.
        snapshot = (canonical({s: saved['stages'][s] for s in INPUT_STAGES + ('SCENE_IR',)})
            if composing_animation else None)
        result = (PedagogyProducerService.status(self, run, tenant)
            if complete or composing_animation else super().status(run, tenant))
        require(not complete or result["stages"]["SCENE_IR"] == "SUCCEEDED", "scene_ir_status_state_changed")
        result["scene_ir"] = None
        verified = None
        if composing_animation:
            require(all(result['stages'][s] == saved['stages'][s]['attempts'][-1]['state']
                for s in INPUT_STAGES + ('SCENE_IR',)), "scene_ir_status_state_changed")
            verified, director_receipt = self._incomplete_status_bundle(run, tenant)
            _, animation_receipt, bundle = verified
            current = self.persistence.load_run_state(run)
            require(canonical({s: current['stages'][s] for s in INPUT_STAGES + ('SCENE_IR',)}) == snapshot,
                "scene_ir_status_state_changed")
            for stage, upstream in (('DIRECTOR', director_receipt), ('VISUAL', bundle['visual_receipt']),
                    ('ANIMATION', animation_receipt)):
                aid, row = self.stage_ref(run, stage)
                require(upstream['output_artifact_id'] == aid and upstream['output_sha256'] == row.blob_digest
                    and upstream['attempt'] == current['stages'][stage]['attempts'][-1]['attempt'],
                    "scene_ir_animation_status_identity")
            final = self.persistence.load_run_state(run)
            require(canonical({s: final['stages'][s]
                for s in INPUT_STAGES + ('SCENE_IR',)}) == snapshot, "scene_ir_status_state_changed")
        if result["stages"]["SCENE_IR"] == "SUCCEEDED":
            verified, director_receipt = self._completed_status_bundle(run, tenant)
            _, receipt, bundle, animation_receipt = verified
        if verified is not None:
            result["director"] = {k: director_receipt[k] for k in ("output_artifact_id", "output_sha256",
                "schema_version", "scene_count", "beat_count", "assessment_count",
                "generation_attempt_count", "critic_attempt_count", "annotation_attempt_count",
                "review_attempt_count", "requires_review", "accepted", "release_ready", "evidence_kind")}
            result["director"].update(validation="PASS", director_executed=True,
                visual_input_validator="NOT_AVAILABLE_FOR_NATIVE_ARTIFACT_PAIR")
            result["live_provider_executed"] = director_receipt["live_provider_executed"]
            result["configured_provider_invoked"] = director_receipt["configured_provider_invoked"]
            visual_receipt = bundle['visual_receipt']
            result['visual'] = {k: visual_receipt[k] for k in ('output_artifact_id', 'output_sha256',
                'schema_version', 'plan_fingerprint', 'visual_intent_count', 'abstention_count',
                'internal_stage_count', 'validation', 'animation_input_compatibility', 'requires_review',
                'accepted', 'release_ready')}
            result['animation'] = {k: animation_receipt[k] for k in ('output_artifact_id', 'output_sha256',
                'schema_version', 'plan_fingerprint', 'track_count', 'internal_stage_count', 'validation',
                'sceneir_handoff_ready', 'requires_review', 'accepted', 'release_ready', 'audio_complete',
                'audio_reconciliation_open')}
        if result["stages"]["SCENE_IR"] == "SUCCEEDED":
            result["scene_ir"] = {k: receipt[k] for k in ("output_artifact_id", "output_sha256", "schema_version",
                "document_fingerprint", "element_count", "track_count", "native_validator_count", "single_scene",
                "validation", "compiler_loader_admitted", "requires_review", "accepted", "release_ready",
                "audio_complete", "audio_reconciliation_open")}
        return result
