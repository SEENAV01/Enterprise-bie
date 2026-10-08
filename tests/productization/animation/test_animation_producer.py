"""Current Visual/Director Animation producer: technical source-derived evidence."""
from contextlib import closing
from copy import deepcopy
from dataclasses import asdict, replace
import gc
import json
from pathlib import Path
import secrets
import shutil
import sqlite3
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
for folder in (ROOT, ROOT / "tests/productization/document_intelligence",
               ROOT / "tests/productization/director", ROOT / "tests/productization/visual",
               Path(__file__).resolve().parent):
    sys.path.insert(0, str(folder))
from test_visual_producer import pdf, target, CHART, TIMELINE, CELL, decoded_strings
from protocol_support import make_stack, config_for_stack
from apps.operator.contracts import Credentials, Principal
from apps.operator.service import Service
from apps.operator.animation_producer import AnimationProducerControlPlane
from bie.productization.contracts import ProducerError, canonical, digest
from bie.productization.animation_contract import PROFILE, profile_config, animation_config, run_identity
from bie.productization.animation_slice import AnimationProducerService, STAGES
from bie.productization.visual_contract import visual_config
from bie.productization.animation_plan import build_current_animation, validate_current_animation
from bie.productization.director_storage import native_runtime
from bie.animation_intelligence.ani_orchestrator import STAGES as INTERNAL


def config(stack=None, *, reduced=False, budget_changes=None):
    stack = make_stack() if stack is None else stack
    budget = dict(profile_id=target()["profile_id"], max_score=20, split_score=35,
                  max_particles=0, max_3d_objects=0, max_asset_bytes=0)
    budget.update(budget_changes or {})
    return profile_config(director=config_for_stack(stack,
        title="Explicit technical Animation source", language="en"),
        visual=visual_config(target()), animation=animation_config(
            reduced_motion_required=reduced, budget=budget))


class AnimationFixture(unittest.TestCase):
    """Every predecessor is produced from native PDF bytes by its real stage."""
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        prepared = getattr(type(self), "_prepared", None)
        if prepared is not None:
            shutil.copytree(prepared.root, self.root, dirs_exist_ok=True)
        self.credentials = Credentials()
        self.token = secrets.token_urlsafe(40)
        self.p = Principal("task035-test", "local", frozenset({"read", "source", "create",
            "worker", "control", "admin_recover"}), time.time() + 900)
        self.credentials.grant(self.token, self.p)
        self.operator = Service(self.root, self.credentials)
        self.stack = make_stack()
        self.config = config(self.stack)
        self.port = AnimationProducerControlPlane(self.operator, enabled_profiles={PROFILE})
        if prepared is None:
            self.source = self.operator.import_pdf(self.p, pdf())
            self.run = self.port.admit(self.p, self.source["source_id"], "intent",
                producer_config=self.config)["run_id"]
        else:
            self.source = self.operator.source(self.p, prepared.source["source_id"])
            self.run = prepared.run
            self.config = deepcopy(prepared.config)

    def tearDown(self):
        gc.collect()
        self.tmp.cleanup()

    def step(self, run=None, **options):
        options["director_stack"] = self.stack
        return self.port.work_once(self.p, run or self.run, **options)

    def until_animation(self):
        result = self.port.status(self.p, self.run)
        for _ in STAGES[:-1]:
            if result["stages"]["ANIMATION"] == "READY":
                break
            result = self.step()
        self.assertEqual(result["stages"]["VISUAL"], "SUCCEEDED", result.get("safe_diagnostics"))
        self.assertEqual(result["stages"]["ANIMATION"], "READY")
        return result

    def complete(self, run=None):
        result = self.port.status(self.p, run or self.run)
        for _ in STAGES:
            if result["slice_complete"] or any(s in ("BLOCKED", "FAILED") for s in result["stages"].values()):
                break
            result = self.step(run)
        return result

    def admit_other(self, lines, key="other", cfg=None):
        source = self.operator.import_pdf(self.p, pdf(lines))
        return self.port.admit(self.p, source["source_id"], key,
            producer_config=cfg or self.config)["run_id"]

    def animation(self, run=None):
        with self.port.native(self.p, run or self.run, "read") as service:
            return service.verified_animation(run or self.run, self.p.tenant)

    def bundle(self):
        with self.port.native(self.p, self.run, "worker") as service:
            return service.animation_inputs(self.run, self.p.tenant, publish=True)

    def tamper_stage(self, stage):
        with self.port.native(self.p, self.run, "read") as service:
            aid, row = service.stage_ref(self.run, stage)
            service.cas._path(row.blob_digest).write_bytes(b"deliberate-cas-tamper")
            return aid

    def assert_failed_animation(self, result):
        self.assertIn(result["stages"]["ANIMATION"], ("BLOCKED", "FAILED"))
        self.assertFalse(result["slice_complete"])
        self.assertIsNone(result["animation"])
        self.assertTrue(all(v == "NOT_RUN" for v in result["downstream"].values()))


class PreparedAnimationFixture(AnimationFixture):
    """Copy closed nine-stage bytes; run actual fresh Animation for each test."""
    PREPARE_COMPLETE = False

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        fixture = AnimationFixture()
        try:
            fixture.setUp()
            if cls.PREPARE_COMPLETE:
                fixture.assertTrue(fixture.complete()["slice_complete"])
            else:
                fixture.until_animation()
        except BaseException:
            if hasattr(fixture, "tmp"):
                fixture.tearDown()
            raise
        cls._prepared = fixture
        cls.addClassCleanup(fixture.tearDown)


class ProfileTests(unittest.TestCase):
    def test_task035_has_ten_ordered_global_stages(self):
        self.assertEqual(STAGES, ("SOURCE", "DOCUMENT_INTELLIGENCE", "KNOWLEDGE", "PREREQUISITE",
            "MATH", "REASONING", "PEDAGOGY", "DIRECTOR", "VISUAL", "ANIMATION"))

    def test_all_historical_profiles_keep_their_exact_scope(self):
        from bie.productization.durable_slice import STAGES as t29
        from bie.productization.reasoning_slice import STAGES as t30
        from bie.productization.math_slice import STAGES as t31
        from bie.productization.pedagogy_slice import STAGES as t32
        from bie.productization.director_slice import STAGES as t33
        from bie.productization.visual_slice import STAGES as t34
        for actual, expected in ((t29, STAGES[:3]), (t30, STAGES[:4] + ("REASONING",)),
                                 (t31, STAGES[:6]), (t32, STAGES[:7]),
                                 (t33, STAGES[:8]), (t34, STAGES[:9])):
            with self.subTest(scope=actual):
                self.assertEqual(actual, expected)

    def test_global_animation_contract_is_unchanged(self):
        stage = AnimationProducerService.graph_for().stages["ANIMATION"]
        self.assertEqual(stage.required_predecessors, ["VISUAL", "DIRECTOR"])
        self.assertEqual(stage.consumes, ["visual.plan", "director.plan"])
        self.assertEqual(stage.emits, "animation.plan")

    def test_profile_has_separate_deterministic_identity(self):
        from bie.productization.visual_contract import run_identity as previous
        self.assertEqual(run_identity("local", "intent"), run_identity("local", "intent"))
        self.assertNotEqual(run_identity("local", "intent"), previous("local", "intent"))

    def test_audio_stage_is_still_unreconciled(self):
        self.assertNotIn("AUDIO", AnimationProducerService.graph_for().stages)

    def test_no_historical_default_reveal_helper_import(self):
        import ast
        for name in ("animation_slice.py", "animation_plan.py", "animation_intents.py"):
            module = ast.parse((ROOT / "bie/productization" / name).read_text(encoding="utf-8"))
            imports = [node.module for node in ast.walk(module) if isinstance(node, ast.ImportFrom)]
            self.assertNotIn("bie.animation_intelligence.ani_actual_e2e", imports)

    def test_native_internal_prefix_is_all_nine_stages(self):
        self.assertEqual(INTERNAL, ("VIS_ADOPT", "SEM", "ATTN", "DOMAIN", "EASE", "TIMELINE",
            "CONTINUITY", "QA", "HANDOFF"))

    def test_budget_profile_must_equal_visual_target(self):
        with self.assertRaises(ProducerError):
            config(budget_changes={"profile_id": "foreign-target"})

    def test_reduced_motion_policy_cannot_be_implicit_or_string(self):
        with self.assertRaises(ProducerError):
            config(reduced="false")

    def test_configuration_cannot_extend_director_timing(self):
        cfg = config()
        self.assertFalse(cfg["animation"]["allow_scene_extension"])
        cfg["animation"]["allow_scene_extension"] = True
        with self.assertRaises(ProducerError):
            profile_config(director=cfg["director"], visual=cfg["visual"], animation=cfg["animation"])

    def test_animation_budget_cannot_be_negative_or_boolean(self):
        for key, value in (("max_score", -1), ("max_particles", True), ("max_asset_bytes", -1)):
            with self.subTest(key=key), self.assertRaises(ProducerError):
                config(budget_changes={key: value})

    def test_animation_budget_cannot_be_unbounded(self):
        with self.assertRaises(ProducerError):
            config(budget_changes={"max_score": 100})


class ActualAnimationTests(AnimationFixture):
    def test_real_pdf_reaches_animation_and_all_internal_stages(self):
        result = self.complete()
        self.assertTrue(result["slice_complete"], result.get("safe_diagnostics"))
        self.assertTrue(all(v == "SUCCEEDED" for v in result["stages"].values()))
        self.assertTrue(all(v == "NOT_RUN" for v in result["downstream"].values()))
        plan, receipt = self.animation()
        self.assertEqual(plan["schema_version"], "1.0.0")
        self.assertTrue(plan["tracks"])
        self.assertFalse(plan["accepted"])
        self.assertEqual(receipt["internal_stage_count"], 9)
        self.assertTrue(receipt["sceneir_handoff_ready"])
        self.assertTrue(receipt["requires_review"])
        self.assertFalse(receipt["accepted"])
        self.assertFalse(receipt["release_ready"])
        self.assertFalse(receipt["product_accepted"])
        self.assertFalse(receipt["scene_ir_executed"])
        self.assertFalse(receipt["audio_complete"])
        self.assertTrue(receipt["audio_reconciliation_open"])
        with self.port.native(self.p, self.run, "read") as service:
            self.assertTrue(all(service.queue.get(service.task_id(self.run, s, 1)).state == "ACKED" for s in STAGES))
            self.assertEqual(service.stage_ref(self.run, "ANIMATION")[1].artifact_type, "animation.plan")

    def test_nonmath_chronology_animation_preserves_order(self):
        # Source order deliberately differs from chronology, and one date is
        # explicitly uncertain. Timing must preserve both distinctions.
        run = self.admit_other(("Timeline: B at 1820; A at about 1810.",), "timeline")
        result = self.complete(run)
        self.assertTrue(result["slice_complete"], result.get("safe_diagnostics"))
        plan, receipt = self.animation(run)
        self.assertTrue(plan["tracks"])
        with self.port.native(self.p, run, "read") as service:
            _, math = service.verified_math(run, service.configuration(run, self.p.tenant))
            self.assertEqual(math["applicability"], "NOT_REQUIRED")
            row = service.read(run, receipt["current_inputs_id"])["rows"][0]
            details = service.read(run, receipt["validation_id"])
        self.assertEqual(row["source_order"], ["B", "A"])
        self.assertEqual(row["semantic_order"], ["A", "B"])
        actual = [item for track in sorted(plan["tracks"], key=lambda t: t["start_ms"])
                  for item in track["payload"]["source_item_ids"]]
        self.assertEqual(actual, row["semantic_order"])
        native = details["outputs"]["DOMAIN"]["plans"][0]
        self.assertTrue(native["source_uncertainty_retained"])
        self.assertFalse(native["chronology"]["ops"][0]["exact_date_claims"])
        self.assertIn("show_uncertainty", native["chronology"]["warnings"])
        self.assertEqual(native["timeline"]["ops"][0]["scale_mode"], "ordinal")
        self.assertTrue(native["timeline"]["ops"][0]["preserve_uncertainty"])

    def test_nonmath_cellular_structure_does_not_invent_flow(self):
        run = self.admit_other((CELL,), "cellular")
        result = self.complete(run)
        self.assertTrue(result["slice_complete"], result.get("safe_diagnostics"))
        plan, receipt = self.animation(run)
        self.assertEqual({t["semantic_action"] for t in plan["tracks"]}, {"emphasize"})
        with self.port.native(self.p, run, "read") as service:
            details = service.read(run, receipt["validation_id"])
            row = service.read(run, receipt["current_inputs_id"])["rows"][0]
        domain = details["outputs"]["DOMAIN"]["plans"][0]
        self.assertFalse(domain["transport_executed"])
        self.assertFalse(domain["physical_motion_claim"])
        self.assertEqual(row["semantic_obligations"]["transports"], [])
        self.assertTrue(domain["native"])
        self.assertEqual({t["payload"]["purpose"] for t in plan["tracks"]}, {"focus"})

    def test_unsupported_math_never_invokes_director_visual_or_animation(self):
        run = self.admit_other(("Compute the matrix inverse.",), "unsupported-math")
        result = self.complete(run)
        self.assertEqual(result["stages"]["MATH"], "BLOCKED")
        for stage in ("REASONING", "PEDAGOGY", "DIRECTOR", "VISUAL", "ANIMATION"):
            self.assertEqual(result["stages"][stage], "PENDING")
        self.assertEqual(self.stack.calls, dict(generator=0, critic=0, annotator=0, reviewer=0))

    def test_visual_semantic_block_prevents_animation(self):
        run = self.admit_other(("The ordinary text has no supported visual declaration.",), "no-visual")
        result = self.complete(run)
        self.assertIn(result["stages"]["VISUAL"], ("BLOCKED", "FAILED"))
        self.assertEqual(result["stages"]["ANIMATION"], "PENDING")
        self.assertIsNone(result["animation"])


class CurrentAnimationTests(PreparedAnimationFixture):
    def test_consumes_exact_persisted_global_and_private_inputs(self):
        self.assertTrue(self.step()["slice_complete"])
        plan, receipt = self.animation()
        with self.port.native(self.p, self.run, "read") as service:
            for stage in ("VISUAL", "DIRECTOR"):
                aid, row = service.stage_ref(self.run, stage)
                self.assertIn(aid, receipt["input_artifact_ids"])
                self.assertIn(row.blob_digest, receipt["input_sha256"])
            _, visual = service.verified_visual(self.run, self.p.tenant)
            self.assertEqual(receipt["visual_handoff_id"], visual["handoff_id"])
            self.assertEqual(plan["visual_plan_fingerprint"], receipt["visual_plan_fingerprint"])

    def test_current_director_sync_is_native_review_only_candidate(self):
        bundle = self.bundle()
        candidate = bundle["candidate"]
        self.assertEqual(candidate.artifact_type, "director.animation_sync_candidate")
        self.assertTrue(candidate.metadata["requires_review"])
        self.assertFalse(candidate.metadata["accepted"])
        self.assertFalse(candidate.metadata["release_ready"])

    def test_animation_does_not_call_model_providers(self):
        self.assertTrue(self.step()["slice_complete"])
        self.assertEqual(self.stack.calls, dict(generator=0, critic=0, annotator=0, reviewer=0))

    def test_identical_intent_replays_exact_artifact_and_queue(self):
        first = self.step()
        identity = self.animation()
        self.assertEqual(self.step(), first)
        self.assertEqual(self.animation(), identity)
        with self.port.native(self.p, self.run, "read") as service:
            self.assertEqual(len(service.persistence.load_run_state(self.run)["stages"]["ANIMATION"]["attempts"]), 1)

    def test_changed_animation_intent_conflicts_under_same_key(self):
        other = config(self.stack, reduced=True)
        with self.assertRaises(Exception):
            self.port.admit(self.p, self.source["source_id"], "intent", producer_config=other)

    def test_safe_projection_has_no_source_narration_or_private_payload(self):
        result = self.step()
        self.assertTrue(result["slice_complete"])
        strings = tuple(decoded_strings(result))
        self.assertFalse(any(CHART in cell for cell in strings))
        self.assertFalse(any(self.token in cell or str(self.root) in cell for cell in strings))
        self.assertFalse(any("source_text" == cell or "narration_text" == cell or "raw_response" == cell for cell in strings))

    def test_native_visual_bytes_tamper_cannot_be_consumed(self):
        self.tamper_stage("VISUAL")
        with self.assertRaises(Exception):
            self.step()

    def test_native_director_bytes_tamper_cannot_be_consumed(self):
        self.tamper_stage("DIRECTOR")
        with self.assertRaises(Exception):
            self.step()

    def test_source_bytes_tamper_cannot_be_consumed(self):
        self.tamper_stage("SOURCE")
        with self.assertRaises(Exception):
            self.step()

    def test_visual_private_handoff_tamper_cannot_be_consumed(self):
        with self.port.native(self.p, self.run, "read") as service:
            _, receipt = service.verified_visual(self.run, self.p.tenant)
            row = service.record(self.run, receipt["handoff_id"])
            service.cas._path(row.blob_digest).write_bytes(b"tampered-handoff")
        with self.assertRaises(Exception):
            self.step()

    def test_final_animation_cas_tamper_fails_readback(self):
        self.assertTrue(self.step()["slice_complete"])
        self.tamper_stage("ANIMATION")
        with self.assertRaises(Exception):
            self.port.status(self.p, self.run)

    def test_no_scene_ir_artifact_is_published(self):
        self.assertTrue(self.step()["slice_complete"])
        with self.port.native(self.p, self.run, "read") as service:
            state = service.persistence.load_run_state(self.run)
            self.assertNotIn("SCENE_IR", state["stages"])
        self.assertEqual(self.port.status(self.p, self.run)["downstream"]["SCENE_IR"], "NOT_RUN")

    def test_foreign_visual_run_rejected(self):
        self.foreign_artifact("VISUAL")

    def test_foreign_director_run_rejected(self):
        self.foreign_artifact("DIRECTOR")

    def foreign_artifact(self, stage):
        with self.port.native(self.p, self.run, "read") as service:
            aid, _ = service.stage_ref(self.run, stage)
            with closing(sqlite3.connect(service.persistence.path)) as db:
                with db:
                    db.execute("UPDATE artifact_records SET run_id='foreign' WHERE artifact_id=?", (aid,))
        with self.assertRaises(Exception):
            self.step()

    def test_foreign_visual_private_handoff_run_rejected(self):
        with self.port.native(self.p, self.run, "read") as service:
            _, receipt = service.verified_visual(self.run, self.p.tenant)
            with closing(sqlite3.connect(service.persistence.path)) as db:
                with db:
                    db.execute("UPDATE artifact_records SET run_id='foreign' WHERE artifact_id=?",
                               (receipt["handoff_id"],))
        with self.assertRaises(Exception):
            self.step()

    def test_superseded_director_revision_blocks_animation(self):
        with self.port.native(self.p, self.run, "read") as service:
            with closing(sqlite3.connect(service.root / "director-state.sqlite3")) as db:
                with db:
                    db.execute("UPDATE director_revisions SET state='STALE' WHERE run_id=?", (self.run,))
        with self.assertRaises(Exception):
            self.step()

    def test_profile_scope_mismatch_fails_closed(self):
        with self.port.native(self.p, self.run, "read") as service:
            with closing(sqlite3.connect(service.persistence.path)) as db:
                with db:
                    db.execute("DELETE FROM attempts WHERE run_id=? AND stage_id='ANIMATION'", (self.run,))
                    db.execute("DELETE FROM stages WHERE run_id=? AND stage_id='ANIMATION'", (self.run,))
        with self.assertRaises(Exception):
            self.port.status(self.p, self.run)

    def remove_visual_parent(self, field):
        with self.port.native(self.p, self.run, "read") as service:
            _, receipt = service.verified_visual(self.run, self.p.tenant)
            attempt = service.persistence.load_run_state(self.run)["stages"]["VISUAL"]["attempts"][-1]
            if field == "receipt":
                aid = attempt["evidence_refs"][0]
            elif field == "internal":
                aid = receipt["internal_record_ids"][0]
            else:
                aid = receipt[field]
            record = service.record(self.run, aid)
            self.assertTrue(record.parent_artifact_ids)
            with closing(sqlite3.connect(service.persistence.path)) as db:
                with db:
                    db.execute("DELETE FROM artifact_parents WHERE artifact_id=? AND parent_artifact_id=?",
                               (aid, record.parent_artifact_ids[0]))
        # Read the Task035 admission API directly so the asserted error comes
        # from its cross-stage lineage gate rather than worker error projection.
        with self.port.native(self.p, self.run, "read") as service:
            with self.assertRaisesRegex(ProducerError, "animation_parent_identity"):
                service.animation_inputs(self.run, self.p.tenant, publish=True)

    def test_visual_current_inputs_parent_tamper_blocks_animation(self):
        self.remove_visual_parent("current_inputs_id")

    def test_visual_handoff_parent_tamper_blocks_animation(self):
        self.remove_visual_parent("handoff_id")

    def test_visual_validation_parent_tamper_blocks_animation(self):
        self.remove_visual_parent("validation_id")

    def test_visual_internal_stage_parent_tamper_blocks_animation(self):
        self.remove_visual_parent("internal")

    def test_visual_receipt_parent_tamper_blocks_animation(self):
        self.remove_visual_parent("receipt")


class GroundedIntentTests(PreparedAnimationFixture):
    def inputs(self):
        from bie.director.director_artifacts import reference
        from bie.director.director_consumers import DirectorConsumers
        from bie.director.director_revisions import DirectorRevisionStore
        from bie.director.director_inputs import load_director_inputs
        with self.port.native(self.p, self.run, "read") as service:
            plan, receipt = service.verified_visual(self.run, self.p.tenant)
            records = service.read(self.run, receipt["current_inputs_id"])["records"]
            handoff = service.read(self.run, receipt["handoff_id"])
            validation = service.read(self.run, receipt["validation_id"])
            output, _ = service.verified_director(self.run, self.p.tenant)
            request, _, _ = service.request(self.run, self.p.tenant)
            with native_runtime(service, self.run, None) as runtime:
                consumers = DirectorConsumers(runtime.io, DirectorRevisionStore(runtime.idempotency))
                _, execution = consumers._director(output.to_ref())
                sync = consumers.read_current(reference(receipt["sync_ref"]))
                inputs = load_director_inputs(runtime.io, request.reasoning_ref, request.pedagogy_ref,
                    lesson_id=request.lesson_id, title=request.title, language=request.language, run_id=self.run)
        return [inputs, execution, sync, records, plan, handoff, validation]

    def derive(self, args=None):
        from bie.productization.animation_intents import derive_animation_intents
        return derive_animation_intents(*(args or self.inputs()), visual_revision=1,
            target_profile=target()["profile_id"])

    def expect_changed_parent_rejected(self, index, mutate):
        args = self.inputs()
        mutate(args[index])
        with self.assertRaises(Exception):
            self.derive(args)

    def test_intents_bind_actual_narration_objective_concept_and_primitive(self):
        typed, rows = self.derive()
        self.assertTrue(typed and rows)
        for intent, row in zip(typed, rows):
            self.assertEqual(intent.binding.anchor.utterance_id, row["anchor"]["utterance_id"])
            self.assertEqual(set(intent.binding.evidence_ids), set(row["evidence_refs"]))
            self.assertEqual(set(intent.binding.objective_ids), set(row["objective_ids"]))
            self.assertEqual(set(intent.binding.concept_ids), set(row["concept_ids"]))
            self.assertTrue(row["reasoning_refs"])
            self.assertEqual({p["primitive_id"] for p in row["primitive_rows"]},
                             {p["timing"]["visual_id"] for p in row["primitive_rows"]})

    def test_primitive_timing_order_does_not_control_identity(self):
        from bie.visual_intelligence.capability_handoff import (
            PrimitiveRequirement, TimingBinding, AssetBinding, build_downstream_handoff)
        args = self.inputs()
        original, rows = self.derive(args)
        raw = args[5]
        reordered = build_downstream_handoff(handoff_id=raw["handoff_id"],
            plan_fingerprint=raw["plan_fingerprint"],
            primitives=tuple(PrimitiveRequirement(**p) for p in reversed(raw["primitives"])),
            assets=tuple(AssetBinding(**p) for p in raw["assets"]),
            timing=tuple(TimingBinding(**p) for p in raw["timing"]),
            accessibility_ready=True, target_capabilities=("2d",), target_profile=raw["target_profile"])
        args[5] = asdict(reordered)
        revised, revised_rows = self.derive(args)
        self.assertEqual([p["primitive_id"] for p in rows[0]["primitive_rows"]],
                         [p["primitive_id"] for p in revised_rows[0]["primitive_rows"]])
        self.assertEqual([p["timing"]["visual_id"] for p in rows[0]["primitive_rows"]],
                         [p["timing"]["visual_id"] for p in revised_rows[0]["primitive_rows"]])
        self.assertEqual([i.kind for i in original], [i.kind for i in revised])

    def test_primitive_timing_id_mismatch_rejected(self):
        self.expect_changed_parent_rejected(5, lambda x: x["timing"][0].update(visual_id="foreign"))

    def test_duplicate_timing_binding_rejected(self):
        self.expect_changed_parent_rejected(5, lambda x: x["timing"].append(deepcopy(x["timing"][0])))

    def test_missing_primitive_lineage_rejected(self):
        self.expect_changed_parent_rejected(5, lambda x: x["primitives"][0].update(source_refs=[]))

    def test_missing_primitive_reasoning_rejected(self):
        self.expect_changed_parent_rejected(5, lambda x: x["primitives"][0].update(reasoning_refs=[]))

    def test_unknown_primitive_target_rejected(self):
        self.expect_changed_parent_rejected(5, lambda x: x["primitives"][0].update(primitive_id="foreign"))

    def test_visual_plan_fingerprint_tamper_rejected(self):
        self.expect_changed_parent_rejected(4, lambda x: x.update(fingerprint="a" * 64))

    def test_visual_handoff_fingerprint_tamper_rejected(self):
        self.expect_changed_parent_rejected(5, lambda x: x.update(handoff_fingerprint="a" * 64))

    def test_stale_visual_revision_rejected(self):
        self.expect_changed_parent_rejected(4, lambda x: x.update(dir_revision=2))

    def test_stale_narration_revision_rejected(self):
        self.expect_changed_parent_rejected(5, lambda x: x["timing"][0].update(narration_revision=2))

    def test_unjustified_motion_semantics_are_not_defaulted_to_reveal(self):
        self.expect_changed_parent_rejected(3, lambda x: x[0].update(semantic_kind="unjustified"))

    def test_descriptive_chart_cannot_become_causal_or_exact(self):
        self.expect_changed_parent_rejected(3,
            lambda x: x[0]["semantic_obligations"].update(exact_curve_claim=True))

    def test_edited_visual_source_values_rejected(self):
        self.expect_changed_parent_rejected(3,
            lambda x: x[0]["semantic_obligations"]["source_items"][0].update(value=9999))

    def test_invented_animation_evidence_rejected_by_independent_derivation(self):
        from bie.productization.animation_intents import validate_derived_animation
        args = self.inputs()
        typed, rows = self.derive(args)
        rows[0]["evidence_refs"] = ["invented-evidence"]
        with self.assertRaises(ProducerError):
            validate_derived_animation(*args, typed, rows, visual_revision=1,
                                      target_profile=target()["profile_id"])

    def test_fake_typed_intent_rejected_by_independent_derivation(self):
        from bie.productization.animation_intents import validate_derived_animation
        args = self.inputs()
        typed, rows = self.derive(args)
        forged = (replace(typed[0], kind="path_follow"),) + typed[1:]
        with self.assertRaises(ProducerError):
            validate_derived_animation(*args, forged, rows, visual_revision=1,
                                      target_profile=target()["profile_id"])

    def sync(self, edit):
        from bie.director.sync_contract import build_sync_context
        from bie.director.narration_visual_sync import sync_visual_intents
        from bie.director.narration_animation_sync import sync_animation_intents
        from bie.productization.visual_intents import derive_intents
        args = self.inputs()
        typed, _ = self.derive(args)
        context = build_sync_context(args[1].speech, args[1].pauses, args[1].emphasis, args[1].timeline)
        visual, _, _ = derive_intents(args[0], args[1])
        return sync_animation_intents(context, sync_visual_intents(context, visual), edit(typed))

    def test_director_rejects_animation_evidence_outside_narration(self):
        with self.assertRaises(Exception):
            self.sync(lambda x: (replace(x[0], binding=replace(x[0].binding, evidence_ids=("foreign",))),))

    def test_director_rejects_animation_objective_outside_narration(self):
        with self.assertRaises(Exception):
            self.sync(lambda x: (replace(x[0], binding=replace(x[0].binding, objective_ids=("foreign",))),))

    def test_director_rejects_unknown_animation_target(self):
        with self.assertRaises(Exception):
            self.sync(lambda x: (replace(x[0], visual_intent_id="foreign"),))

    def test_general_director_sync_rejects_equation_morph_shortcut(self):
        with self.assertRaises(Exception):
            self.sync(lambda x: (replace(x[0], kind="morph"),))

    def test_same_target_property_conflict_blocks(self):
        result = self.sync(lambda x: (x[0], replace(x[0],
            binding=replace(x[0].binding, intent_id="second-motion"))))
        self.assertIn("ANIMATION_PROPERTY_CONFLICT", {issue.code for issue in result.issues})

    def test_cyclic_animation_dependencies_rejected(self):
        def cycle(x):
            second = replace(x[0], binding=replace(x[0].binding, intent_id="second-motion"),
                             after_intent_ids=(x[0].binding.intent_id,))
            return replace(x[0], after_intent_ids=("second-motion",)), second
        with self.assertRaisesRegex(ValueError, "cycle"):
            self.sync(cycle)

    def test_unfinished_dependency_blocks(self):
        result = self.sync(lambda x: (x[0], replace(x[0],
            binding=replace(x[0].binding, intent_id="second-motion"),
            after_intent_ids=(x[0].binding.intent_id,))))
        self.assertIn("DEPENDENCY_NOT_FINISHED", {issue.code for issue in result.issues})

    def test_animation_minimum_duration_cannot_escape_narration(self):
        result = self.sync(lambda x: (replace(x[0], minimum_duration_ms=999999),))
        self.assertIn("ANIMATION_WINDOW_TOO_SHORT", {issue.code for issue in result.issues})

    def test_audio_replan_is_a_hard_admission_blocker(self):
        from bie.director.sync_contract import SyncIssue
        from bie.productization.animation_slice import check_sync
        result = self.sync(lambda x: x)
        result = replace(result, issues=(SyncIssue("AUDIO_REPLAN_REQUIRED", "audio", "technical", "DIR_TIME"),))
        with self.assertRaisesRegex(ProducerError, "animation_audio_replan_required"):
            check_sync(result)


class CommittedAnimationTests(PreparedAnimationFixture):
    PREPARE_COMPLETE = True

    def forged_receipt(self, **changes):
        _, receipt = self.animation()
        forged = dict(receipt, **changes)
        with self.port.native(self.p, self.run, "worker") as service:
            attempt = service.persistence.load_run_state(self.run)["stages"]["ANIMATION"]["attempts"][-1]
            old = service.record(self.run, attempt["evidence_refs"][0])
            aid = service.put(self.run, "ANIMATION", "producer.evidence", forged, old.parent_artifact_ids, True)
            self.assertEqual(service.read(self.run, aid), forged)
            with closing(sqlite3.connect(service.persistence.path)) as db:
                with db:
                    db.execute("UPDATE attempts SET evidence_refs_json=? WHERE run_id=? AND stage_id='ANIMATION' AND attempt=?",
                               (json.dumps([aid]), self.run, attempt["attempt"]))
        with self.assertRaises(ProducerError):
            self.port.status(self.p, self.run)

    def test_valid_cas_receipt_cannot_self_accept(self):
        self.forged_receipt(accepted=True)

    def test_valid_cas_receipt_cannot_remove_review(self):
        self.forged_receipt(requires_review=False)

    def test_valid_cas_receipt_cannot_promote_release_readiness(self):
        self.forged_receipt(release_ready=True)

    def test_valid_cas_receipt_cannot_claim_audio_complete(self):
        self.forged_receipt(audio_complete=True)

    def test_valid_cas_receipt_cannot_claim_scene_ir_execution(self):
        self.forged_receipt(scene_ir_executed=True)

    def test_valid_cas_receipt_cannot_claim_product_acceptance(self):
        self.forged_receipt(product_accepted=True)

    def test_stale_replay_currentness_token_rejected(self):
        _, receipt = self.animation()
        replay = dict(receipt["replay"], currentness_token="a" * 64)
        self.forged_receipt(replay=replay)

    def test_private_source_field_cannot_leak_through_receipt(self):
        self.forged_receipt(private_source=CHART)

    def remove_support_parent(self, field):
        _, receipt = self.animation()
        with self.port.native(self.p, self.run, "read") as service:
            attempt = service.persistence.load_run_state(self.run)["stages"]["ANIMATION"]["attempts"][-1]
            aid = attempt["evidence_refs"][0] if field == "receipt" else receipt[field]
            record = service.record(self.run, aid)
            self.assertTrue(record.parent_artifact_ids)
            with closing(sqlite3.connect(service.persistence.path)) as db:
                with db:
                    db.execute("DELETE FROM artifact_parents WHERE artifact_id=? AND parent_artifact_id=?",
                               (aid, record.parent_artifact_ids[0]))
        with self.assertRaisesRegex(ProducerError, "animation_parent_identity"):
            self.port.status(self.p, self.run)

    def test_current_inputs_parent_link_tamper_rejected(self):
        self.remove_support_parent("current_inputs_id")

    def test_validation_parent_link_tamper_rejected(self):
        self.remove_support_parent("validation_id")

    def test_handoff_parent_link_tamper_rejected(self):
        self.remove_support_parent("handoff_id")

    def test_safe_receipt_parent_link_tamper_rejected(self):
        self.remove_support_parent("receipt")

    def test_reordered_global_inputs_cannot_be_laundered_through_new_receipt(self):
        _, receipt = self.animation()
        forged = deepcopy(receipt)
        forged["input_artifact_ids"].reverse()
        forged["input_sha256"].reverse()
        with self.port.native(self.p, self.run, "worker") as service:
            attempt = service.persistence.load_run_state(self.run)["stages"]["ANIMATION"]["attempts"][-1]
            old = service.record(self.run, attempt["evidence_refs"][0])
            aid = service.put(self.run, "ANIMATION", "producer.evidence", forged, old.parent_artifact_ids, True)
            with closing(sqlite3.connect(service.persistence.path)) as db:
                with db:
                    db.execute("UPDATE attempts SET input_refs_json=?, evidence_refs_json=? WHERE run_id=? AND stage_id='ANIMATION' AND attempt=?",
                        (json.dumps(forged["input_artifact_ids"]), json.dumps([aid]), self.run, attempt["attempt"]))
        with self.assertRaisesRegex(ProducerError, "animation_upstream_identity"):
            self.port.status(self.p, self.run)


class PlanningSafetyTests(PreparedAnimationFixture):
    def build(self, bundle=None, settings=None):
        bundle = self.bundle() if bundle is None else bundle
        return build_current_animation(bundle["rows"], settings or self.config["animation"],
            run_id=self.run, handoff=bundle["handoff"])

    def test_plan_has_real_full_prefix_qa_trace_and_handoff(self):
        plan, handoff, details = self.build()
        self.assertEqual(tuple(r["stage"] for r in details["stages"]), INTERNAL)
        self.assertEqual(handoff.animation_plan_fingerprint, plan.plan_fingerprint)
        self.assertTrue(details["qa"]["trace"]["passed"])
        self.assertEqual({n.track_id for n in handoff.nodes}, {t.track_id for t in plan.tracks})
        for key in ("purpose", "synchronization", "temporal", "motion", "accessibility"):
            self.assertIn(details["qa"][key]["status"], ("PASS", "REVIEW"))
        self.assertEqual(details["qa"]["performance"]["action"], "PASS")
        self.assertFalse(details["outputs"]["SEM"]["default_reveal_used"])
        self.assertFalse(details["outputs"]["SEM"]["positional_timing_used"])

    def test_static_axis_has_explicit_abstention_and_no_track(self):
        plan, _, details = self.build()
        abstained = {a["primitive_id"] for a in details["outputs"]["VIS_ADOPT"]["abstentions"]}
        self.assertTrue(abstained)
        self.assertFalse(abstained.intersection(t for track in plan.tracks for t in track.target_ids))

    def test_duration_never_extends_current_scene(self):
        bundle = self.bundle()
        plan, _, details = self.build(bundle)
        self.assertEqual(plan.scene_end_ms, max(r["scene_end_ms"] for r in bundle["rows"]))
        self.assertFalse(details["outputs"]["EASE"]["scene_extension_allowed"])
        self.assertTrue(all(t.end_ms <= t.payload["timing_binding"]["end_ms"] for t in plan.tracks))

    def test_changed_purpose_cannot_reuse_source_action(self):
        bundle = self.bundle()
        bundle["rows"][0]["purpose"] = "show_change"
        with self.assertRaisesRegex(ProducerError, "animation_purpose_action_mismatch"):
            self.build(bundle)

    def test_missing_action_cannot_default_to_reveal(self):
        bundle = self.bundle()
        bundle["rows"][0]["action"] = None
        with self.assertRaisesRegex(ProducerError, "animation_unsupported_action"):
            self.build(bundle)

    def test_equation_morph_without_authoritative_obligations_is_not_admitted(self):
        bundle = self.bundle()
        bundle["rows"][0]["action"] = "morph"
        with self.assertRaisesRegex(ProducerError, "animation_unsupported_action"):
            self.build(bundle)

    def test_simulation_without_authoritative_model_is_not_admitted(self):
        bundle = self.bundle()
        bundle["rows"][0]["semantic_kind"] = "simulation"
        bundle["rows"][0]["action"] = "simulation_state"
        with self.assertRaisesRegex(ProducerError, "animation_unsupported_domain"):
            self.build(bundle)

    def test_unknown_primitive_cannot_acquire_track(self):
        bundle = self.bundle()
        bundle["rows"][0]["primitive_rows"][0]["primitive_id"] = "foreign"
        with self.assertRaises(ProducerError):
            self.build(bundle)

    def test_window_outside_scene_rejected(self):
        bundle = self.bundle()
        bundle["rows"][0]["scene_end_ms"] = 1
        with self.assertRaisesRegex(ProducerError, "animation_track_outside_scene"):
            self.build(bundle)

    def test_window_outside_narration_rejected(self):
        bundle = self.bundle()
        bundle["rows"][0]["window"]["end_ms"] += 100
        with self.assertRaises(ProducerError):
            self.build(bundle)

    def test_policy_duration_failure_does_not_clip_or_extend(self):
        from bie.animation_intelligence.duration_rules import resolve_duration
        def fail(context, **kwargs):
            return resolve_duration(context, narration_window_ms=1, allow_scene_extension=False)
        with patch("bie.productization.animation_plan.resolve_duration", side_effect=fail):
            with self.assertRaisesRegex(ProducerError, "animation_duration_blocked"):
                self.build()

    def test_unsatisfiable_timeline_cannot_publish_partial_plan(self):
        from bie.animation_intelligence.global_timeline_solver import TimelineResult
        with patch("bie.productization.animation_plan.solve", return_value=TimelineResult((), ("technical-unsat",), False)):
            with self.assertRaisesRegex(ProducerError, "animation_timeline_unsat"):
                self.build()

    def test_native_action_change_is_rejected(self):
        from bie.animation_intelligence.reveal_selection import select_reveal
        def changed(context, **kwargs):
            value = select_reveal(context, **kwargs)
            return replace(value, steps=(replace(value.steps[0], action="morph"),))
        with patch("bie.productization.animation_plan.select_reveal", side_effect=changed):
            with self.assertRaisesRegex(ProducerError, "animation_native_motion_mismatch"):
                self.build()

    def test_native_motion_cannot_invent_source_state(self):
        from bie.animation_intelligence.reveal_selection import select_reveal
        def changed(context, **kwargs):
            value = select_reveal(context, **kwargs)
            return replace(value, steps=(replace(value.steps[0], source_state_id="foreign-state"),))
        with patch("bie.productization.animation_plan.select_reveal", side_effect=changed):
            with self.assertRaisesRegex(ProducerError, "animation_native_state_mismatch"):
                self.build()

    def test_native_motion_cannot_invent_target_state(self):
        from bie.animation_intelligence.reveal_selection import select_reveal
        def changed(context, **kwargs):
            value = select_reveal(context, **kwargs)
            return replace(value, steps=(replace(value.steps[0], target_state_id="foreign-state"),))
        with patch("bie.productization.animation_plan.select_reveal", side_effect=changed):
            with self.assertRaisesRegex(ProducerError, "animation_native_state_mismatch"):
                self.build()

    def test_native_motion_cannot_invent_semantic_effect(self):
        from bie.animation_intelligence.reveal_selection import select_reveal
        def changed(context, **kwargs):
            value = select_reveal(context, **kwargs)
            return replace(value, steps=(replace(value.steps[0], semantic_effect="invented_transport"),))
        with patch("bie.productization.animation_plan.select_reveal", side_effect=changed):
            with self.assertRaisesRegex(ProducerError, "animation_native_state_mismatch"):
                self.build()

    def test_native_motion_cannot_smuggle_untracked_payload(self):
        from bie.animation_intelligence.reveal_selection import select_reveal
        def changed(context, **kwargs):
            value = select_reveal(context, **kwargs)
            return replace(value, steps=(replace(value.steps[0],
                payload=dict(value.steps[0].payload, invented_motion="transport")),))
        with patch("bie.productization.animation_plan.select_reveal", side_effect=changed):
            with self.assertRaisesRegex(ProducerError, "animation_native_state_mismatch"):
                self.build()

    def assert_native_qa_block_prevents_plan(self, alias, code):
        from bie.animation_intelligence.qa_contracts import result
        blocked = result("technical-negative", "BLOCKED", blockers=("technical-negative",))
        with patch("bie.productization.animation_plan." + alias, return_value=blocked):
            with self.assertRaisesRegex(ProducerError, code):
                self.build()

    def test_purpose_qa_blocks_animation_plan(self):
        self.assert_native_qa_block_prevents_plan("purpose_qa", "animation_purpose_qa_blocked")

    def test_synchronization_qa_blocks_animation_plan(self):
        self.assert_native_qa_block_prevents_plan("synchronization_qa", "animation_sync_qa_blocked")

    def test_temporal_conflict_qa_blocks_animation_plan(self):
        self.assert_native_qa_block_prevents_plan("temporal_qa", "animation_temporal_qa_blocked")

    def test_excessive_motion_qa_blocks_animation_plan(self):
        self.assert_native_qa_block_prevents_plan("motion_qa", "animation_motion_qa_blocked")

    def test_native_flash_violation_blocks_animation_plan(self):
        from bie.animation_intelligence.ani_accessibility import enforce_animation_accessibility
        def fail(tracks, policy):
            return enforce_animation_accessibility(
                [replace(t, payload=dict(t.payload, flash_hz=4)) for t in tracks], policy)
        with patch("bie.productization.animation_plan.enforce_animation_accessibility", side_effect=fail):
            with self.assertRaisesRegex(ProducerError, "animation_accessibility_blocked"):
                self.build()

    def test_missing_reduced_motion_variant_blocks_animation_plan(self):
        from bie.animation_intelligence.ani_accessibility import enforce_animation_accessibility, AccessibilityPolicy
        def fail(tracks, policy):
            return enforce_animation_accessibility(
                [replace(t, semantic_action="camera", reduced_motion_variant=None) for t in tracks],
                AccessibilityPolicy(True))
        with patch("bie.productization.animation_plan.enforce_animation_accessibility", side_effect=fail):
            with self.assertRaisesRegex(ProducerError, "animation_accessibility_blocked"):
                self.build()

    def test_unrealized_reduced_motion_replacement_cannot_be_claimed_ready(self):
        from bie.animation_intelligence.ani_accessibility import AccessibilityResult
        result = AccessibilityResult("PASS", (("track", "static_focus"),), (), ())
        with patch("bie.productization.animation_plan.enforce_animation_accessibility", return_value=result):
            with self.assertRaisesRegex(ProducerError, "animation_reduced_motion_realization_required"):
                self.build()

    def test_explicit_performance_budget_is_enforced_without_track_loss(self):
        bundle = self.bundle()
        settings = deepcopy(self.config["animation"])
        settings["budget"]["max_score"] = .01
        with self.assertRaisesRegex(ProducerError, "animation_performance_blocked"):
            self.build(bundle, settings)

    def test_native_trace_blocker_prevents_plan(self):
        from bie.animation_intelligence.ani_trace_matrix import TraceAudit
        with patch("bie.productization.animation_plan.audit_trace", return_value=TraceAudit((), ("missing_source",), False)):
            with self.assertRaises(Exception):
                self.build()

    def test_native_continuity_failure_prevents_plan(self):
        from bie.animation_intelligence.continuity_ledger import ContinuityError
        with patch("bie.productization.animation_plan.ContinuityLedger.add", side_effect=ContinuityError("unauthorized identity")):
            with self.assertRaises(ContinuityError):
                self.build()

    def test_unsupported_sceneir_handoff_action_prevents_success(self):
        from bie.animation_intelligence.ani_sceneir_handoff import build_sceneir_handoff
        def fail(plan):
            return build_sceneir_handoff(replace(plan, tracks=tuple(
                replace(t, semantic_action="unsupported-motion", reduced_motion_variant=None) for t in plan.tracks)))
        with patch("bie.productization.animation_plan.build_sceneir_handoff", side_effect=fail):
            with self.assertRaises(Exception):
                self.build()

    def test_plan_fingerprint_tamper_rejected_by_independent_recomposition(self):
        bundle = self.bundle()
        plan, handoff, details = self.build(bundle)
        raw = asdict(plan)
        raw["plan_fingerprint"] = "a" * 64
        with self.assertRaisesRegex(ProducerError, "animation_plan_identity_mismatch"):
            validate_current_animation(bundle["rows"], self.config["animation"], run_id=self.run,
                handoff=bundle["handoff"], plan_dict=raw, handoff_dict=asdict(handoff), details=details)

    def test_plan_cannot_self_accept_on_reconstruction(self):
        bundle = self.bundle()
        plan, handoff, _ = self.build(bundle)
        raw = dict(asdict(plan), accepted=True)
        with self.assertRaisesRegex(ProducerError, "animation_acceptance_promoted"):
            validate_current_animation(bundle["rows"], self.config["animation"], run_id=self.run,
                handoff=bundle["handoff"], plan_dict=raw, handoff_dict=asdict(handoff))

    def test_sceneir_handoff_fingerprint_tamper_rejected(self):
        bundle = self.bundle()
        plan, handoff, _ = self.build(bundle)
        raw = dict(asdict(handoff), animation_plan_fingerprint="a" * 64)
        with self.assertRaisesRegex(ProducerError, "animation_handoff_identity_mismatch"):
            validate_current_animation(bundle["rows"], self.config["animation"], run_id=self.run,
                handoff=bundle["handoff"], plan_dict=asdict(plan), handoff_dict=raw)

    def test_source_grounded_reduced_motion_configuration_succeeds(self):
        settings = deepcopy(self.config["animation"])
        settings["reduced_motion_required"] = True
        plan, _, details = self.build(settings=settings)
        self.assertTrue(plan.reduced_motion_requested)
        self.assertEqual(details["qa"]["accessibility"]["status"], "PASS")


if __name__ == "__main__":
    unittest.main()
