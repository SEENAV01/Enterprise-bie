"""Current source/Director Visual production controls; technical evidence only."""
from contextlib import closing, contextmanager
from copy import deepcopy
from dataclasses import asdict, replace
from hashlib import sha256
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
               ROOT / "tests/productization/director", Path(__file__).resolve().parent):
    sys.path.insert(0, str(folder))
from structural_pdf_fixtures import positioned_text_pdf
from protocol_support import make_stack, config_for_stack
from apps.operator.contracts import Credentials, Principal
from apps.operator.service import Service
from apps.operator.visual_producer import VisualProducerControlPlane
from bie.productization.contracts import ProducerError, canonical, digest
from bie.productization.visual_contract import PROFILE, profile_config, run_identity, visual_config
from bie.productization.visual_slice import VisualProducerService, STAGES
from bie.productization.visual_plan import build_current_plan, validate_current_plan
from bie.productization.director_storage import native_runtime
from bie.director.director_consumers import DirectorConsumers
from bie.director.director_revisions import DirectorRevisionStore
from bie.director.narration_visual_sync import sync_visual_intents
from bie.director.sync_contract import build_sync_context
from bie.director.director_inputs import load_director_inputs
from bie.productization.visual_intents import derive_intents, validate_derived, parse_declaration
from bie.visual_intelligence.visual_plan_contract import STAGES as INTERNAL, VisualPlan
from bie.animation_intelligence.vis_ani_adoption import adopt_visual_handoff


CHART = "Chart B x A y B: C 2; D 3."
TIMELINE = "Timeline: A at 1810; B at 1820."
CELL = "Cell: A C; B C."


def pdf(lines=(CHART,)):
    return positioned_text_pdf([[(72, 740 - 40 * i, text) for i, text in enumerate(lines)]])


def target(**changes):
    value = dict(profile_id="task034-technical-2d", capabilities=["2d", "math_text"],
        max_complexity=1.0, supports_interaction=False, supports_3d=False,
        supports_simulation=False, viewport_width=1280, viewport_height=720,
        font_px=24, foreground="#111111", background="#FFFFFF")
    value.update(changes)
    return value


def config(stack=None, **target_changes):
    stack = make_stack() if stack is None else stack
    return profile_config(director=config_for_stack(stack,
        title="Explicit technical Visual source", language="en"),
        visual=visual_config(target(**target_changes)))


def decoded_strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for key, cell in value.items():
            yield from decoded_strings(key)
            yield from decoded_strings(cell)
    elif isinstance(value, (tuple, list)):
        for cell in value:
            yield from decoded_strings(cell)


class VisualFixture(unittest.TestCase):
    """Genuine PDF and durable native predecessor runtime, never fixture intents."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        prepared = getattr(type(self), "_prepared", None)
        if prepared is not None:
            shutil.copytree(prepared.root, self.root, dirs_exist_ok=True)
        self.credentials = Credentials()
        self.token = secrets.token_urlsafe(40)
        self.p = Principal("task034-test", "local", frozenset({"read", "source", "create",
            "worker", "control", "admin_recover"}), time.time() + 900)
        self.credentials.grant(self.token, self.p)
        self.operator = Service(self.root, self.credentials)
        self.stack = make_stack()
        self.config = config(self.stack)
        self.port = VisualProducerControlPlane(self.operator, enabled_profiles={PROFILE})
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

    def step(self, run=None, *, providers=True, **options):
        if providers:
            options["director_stack"] = self.stack
        return self.port.work_once(self.p, run or self.run, **options)

    def until_visual(self):
        result = self.port.status(self.p, self.run)
        for _ in STAGES[:-1]:
            if result["stages"]["VISUAL"] == "READY":
                break
            result = self.step()
        self.assertEqual(result["stages"]["DIRECTOR"], "SUCCEEDED")
        self.assertEqual(result["stages"]["VISUAL"], "READY")
        return result

    def complete(self, run=None, *, providers=True):
        result = self.port.status(self.p, run or self.run)
        for _ in STAGES:
            if result["slice_complete"] or any(v in ("FAILED", "BLOCKED") for v in result["stages"].values()):
                break
            result = self.step(run, providers=providers)
        return result

    def admit_other(self, lines, key="other", cfg=None):
        source = self.operator.import_pdf(self.p, pdf(lines))
        return self.port.admit(self.p, source["source_id"], key,
            producer_config=cfg or self.config)["run_id"]

    def visual(self, run=None):
        with self.port.native(self.p, run or self.run, "read") as service:
            return service.verified_visual(run or self.run, self.p.tenant)

    def tamper_stage(self, stage):
        with self.port.native(self.p, self.run, "read") as service:
            aid, row = service.stage_ref(self.run, stage)
            service.cas._path(row.blob_digest).write_bytes(b"deliberate-cas-tamper")
            return aid

    def current_inputs(self):
        with self.port.native(self.p, self.run, "worker") as service:
            return service.current_inputs(self.run, self.p.tenant, publish=True)

    def assert_failed_visual(self, result, code=None):
        self.assertIn(result["stages"]["VISUAL"], ("FAILED", "BLOCKED"))
        self.assertFalse(result["slice_complete"])
        self.assertIsNone(result["visual"])
        if code:
            self.assertIn(code, result["safe_diagnostics"]["VISUAL"])
        self.assertTrue(all(s == "NOT_RUN" for s in result["downstream"].values()))


class PreparedVisualFixture(VisualFixture):
    """Reuse closed predecessor bytes only; every Visual execution is current."""
    PREPARE_COMPLETE = False

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        fixture = VisualFixture()
        try:
            fixture.setUp()
            if cls.PREPARE_COMPLETE:
                fixture.assertTrue(fixture.complete()["slice_complete"])
            else:
                fixture.until_visual()
        except BaseException:
            if hasattr(fixture, "tmp"):
                fixture.tearDown()
            raise
        cls._prepared = fixture
        cls.addClassCleanup(fixture.tearDown)


class ProfileAndPreservationTests(unittest.TestCase):
    def test_nine_stage_scope(self):
        self.assertEqual(STAGES, ("SOURCE", "DOCUMENT_INTELLIGENCE", "KNOWLEDGE", "PREREQUISITE",
            "MATH", "REASONING", "PEDAGOGY", "DIRECTOR", "VISUAL"))

    def test_task029_scope_remains_three(self):
        from bie.productization.durable_slice import STAGES as old
        self.assertEqual(old, STAGES[:3])

    def test_task030_scope_remains_five(self):
        from bie.productization.reasoning_slice import STAGES as old
        self.assertEqual(old, ("SOURCE", "DOCUMENT_INTELLIGENCE", "KNOWLEDGE", "PREREQUISITE", "REASONING"))

    def test_task031_scope_remains_six(self):
        from bie.productization.math_slice import STAGES as old
        self.assertEqual(old, STAGES[:6])

    def test_task032_scope_remains_seven(self):
        from bie.productization.pedagogy_slice import STAGES as old
        self.assertEqual(old, STAGES[:7])

    def test_task033_scope_remains_eight(self):
        from bie.productization.director_slice import STAGES as old
        self.assertEqual(old, STAGES[:8])

    def test_existing_visual_graph_contract(self):
        stage = VisualProducerService.graph_for().stages["VISUAL"]
        self.assertEqual(stage.required_predecessors, ["DIRECTOR", "REASONING"])
        self.assertEqual(stage.consumes, ["director.plan", "reasoning.decision_set"])
        self.assertEqual(stage.emits, "visual.plan")

    def test_audio_remains_open(self):
        self.assertNotIn("AUDIO", VisualProducerService.graph_for().stages)

    def test_distinct_deterministic_profile_identity(self):
        from bie.productization.director_contract import run_identity as old
        self.assertEqual(run_identity("local", "intent"), run_identity("local", "intent"))
        self.assertNotEqual(run_identity("local", "intent"), old("local", "intent"))

    def test_explicit_target_required(self):
        with self.assertRaises(ProducerError):
            visual_config({})

    def test_target_wrong_field_rejected(self):
        with self.assertRaises(ProducerError):
            visual_config(target(untracked=True))

    def test_target_duplicate_capability_rejected(self):
        with self.assertRaises(ProducerError):
            visual_config(target(capabilities=["2d", "2d"]))

    def test_target_boolean_dimensions_rejected(self):
        with self.assertRaises(ProducerError):
            visual_config(target(viewport_width=True))

    def test_target_outside_resource_bounds_rejected(self):
        with self.assertRaises(ProducerError):
            visual_config(target(viewport_width=8192))

    def test_target_noncolor_rejected(self):
        with self.assertRaises(ProducerError):
            visual_config(target(foreground="untracked-style"))

    def test_visual_policy_tamper_rejected(self):
        value = visual_config(target())
        value["policy"] = "invented"
        with self.assertRaises(ProducerError):
            profile_config(director=config_for_stack(), visual=value)

    def test_historical_dir_pins_are_unchanged(self):
        from bie.visual_intelligence.canonical_dir_codec import CANONICAL_DIR_COMMIT, CANONICAL_DIR_TREE
        self.assertEqual(CANONICAL_DIR_COMMIT, "73840d86a78e5f31438e2a1bad34f3b2a8433eb9")
        self.assertEqual(CANONICAL_DIR_TREE, "adf64727adaf2ec9dd92c8f1ea03e2df2b8d738c")

    def test_historical_rep_archive_pin_identity(self):
        from bie.visual_intelligence.rep_original_codec import EXPECTED_REP_ARCHIVE_SHA256
        self.assertEqual(digest(EXPECTED_REP_ARCHIVE_SHA256),
            digest({"BIE_VIS_REP_001.zip": "e16246c98c9e27d4b0b5761ab15d05efaf96abc5498e833e1ac30d53eeb81a9f",
                "BIE_VIS_REP_002.zip": "60bacbcab47ed1725a06772b75a8ce5eb3a87edb298a80949aea9c731b88d492",
                "BIE_VIS_REP_003.zip": "eabfe0872416ab7077d6f07698773e3f7d64f4aba7e3ca0e0c3817cee39e35fc",
                "BIE_VIS_REP_004.zip": "e88249affc0dc401ca7641ac30aae284a9deb6025cac494c5d25e10f7a896e5c",
                "BIE_VIS_REP_005.zip": "4f8a5c0a0989bcb6c2bbcf9dd1247a6ebfe11c39edf74e91f9c49442b4d6e942",
                "BIE_VIS_REP_006.zip": "4e6d8445741b274916b74df577df04541e0dc6992269a8290074c79c7ef574f0",
                "BIE_VIS_REP_007.zip": "14d9670c170822556c76b0f8ca7c76c00f9acd789358bb66a9e2fa976e3eb8c2",
                "BIE_VIS_REP_008.zip": "017be204a6082e01242b3d4bc60b47b310fe29e2e0b9bebe357e9fc38de32ccf"}))

    def test_original_global_graph_and_task028_bytes_preserved(self):
        expected = {"bie/infrastructure/execution_graph.py": "dbe9df946b92fa28b539559bd6d7aead915d1f67b360be427108a616008fe464",
            "apps/api/job_service.py": "7fc9d24070f7a91a3da455dcf7b34aad76077688f27609424780e329518a09a1",
            "apps/api/pdf_worker_service.py": "9d045eb78ed2454fea60f93d1e8ba98b753781662f58b6a93109eac60cae837e",
            "scripts/run_bie_pdf_worker.py": "9186919395dd1795e80487779548e5552d970f929712a7883d51d75290eb41d6",
            "scripts/run_bie_local_stack.py": "be5047bc97b43961fd9a504b6b1c75138948404419a7457ef83eb9d6197a1b49"}
        for name, identity in expected.items():
            with self.subTest(file=name):
                self.assertEqual(sha256((ROOT / name).read_bytes().replace(b"\r\n", b"\n")).hexdigest(), identity)

    def test_native_visual_director_animation_sceneir_and_android_trees_preserved(self):
        expected = {"apps/android": (33, "2f84b313cb6bf380157339adb626800362832d376426d7c66002ca90a992faa7"),
            "bie/visual_intelligence": (84, "c9ec6588f00b3cce8b16f340a7940bff57a7d74e8f7d2fa83fc10ff204817544"),
            "bie/director": (71, "62abca7d4f1f613aa38907128f528bccddb2e3c1bfeb105cdf2ba79599d93824"),
            "bie/animation_intelligence": (67, "d34eedf95497788585dd42a54b45cbfbc7a6d3c5808aa85707ce172743598252"),
            "bie/scene_ir": (80, "21c2c479c1b1880e43f0f9ba0f0f4685bafd0ec374985932b9c67f480066e3c0")}
        for folder, (count, identity) in expected.items():
            paths = sorted(p for p in (ROOT / folder).rglob("*") if p.is_file() and
                "__pycache__" not in p.parts and ".gradle" not in p.parts)
            items = [(p.relative_to(ROOT).as_posix(), sha256(p.read_bytes().replace(b"\r\n", b"\n")).hexdigest())
                     for p in paths]
            with self.subTest(folder=folder):
                self.assertEqual(len(items), count)
                self.assertEqual(sha256(json.dumps(items, sort_keys=True, separators=(",", ":")).encode()).hexdigest(), identity)


class ActualProducerTests(VisualFixture):
    def test_actual_pdf_reaches_all_nine_stages_with_native_qa(self):
        result = self.complete()
        self.assertTrue(result["slice_complete"], result.get("safe_diagnostics"))
        self.assertTrue(all(v == "SUCCEEDED" for v in result["stages"].values()))
        self.assertTrue(all(v == "NOT_RUN" for v in result["downstream"].values()))
        plan, receipt = self.visual()
        self.assertEqual(tuple(row["stage"] for row in plan["stages"]), INTERNAL)
        self.assertTrue(plan["review_required"])
        self.assertFalse(plan["accepted"])
        self.assertFalse(receipt["release_ready"])
        self.assertFalse(receipt["historical_dir_runtime_claimed"])
        self.assertFalse(receipt["historical_rep_archive_runtime_claimed"])
        self.assertGreater(self.stack.calls["generator"], 0)
        self.assertGreater(self.stack.calls["critic"], 0)
        with self.port.native(self.p, self.run, "read") as service:
            details = service.read(self.run, receipt["validation_id"])
            self.assertTrue(details)
            self.assertTrue(all(row["semantic_qa"]["passed"] and row["semantic_policies"]["passed"] and
                row["layout_qa"]["passed"] and row["asset_qa"]["passed"] and
                not row["accessibility"]["blocked"] for row in details))
            self.assertTrue(all(service.queue.get(service.task_id(self.run, s, 1)).state == "ACKED" for s in STAGES))

    def test_nonmath_timeline_uses_chronology_grammar(self):
        run = self.admit_other((TIMELINE,), "timeline")
        result = self.complete(run)
        self.assertTrue(result["slice_complete"], result.get("safe_diagnostics"))
        plan, receipt = self.visual(run)
        with self.port.native(self.p, run, "read") as service:
            details = service.read(run, receipt["validation_id"])
            self.assertEqual(details[0]["grammar"]["grammar_id"], "bie.vis.grammar.history_timeline")
            _, math = service.verified_math(run, service.configuration(run, "local"))
            self.assertEqual(math["applicability"], "NOT_REQUIRED")
        self.assertFalse(plan["accepted"])

    def test_nonmath_cellular_uses_structural_grammar(self):
        run = self.admit_other((CELL,), "cellular")
        result = self.complete(run)
        self.assertTrue(result["slice_complete"], result.get("safe_diagnostics"))
        _, receipt = self.visual(run)
        with self.port.native(self.p, run, "read") as service:
            details = service.read(run, receipt["validation_id"])
            self.assertEqual(details[0]["grammar"]["grammar_id"], "bie.vis.grammar.biology_cellular")

    def test_changed_source_changes_persisted_visual_identity(self):
        self.assertTrue(self.complete()["slice_complete"])
        first, first_receipt = self.visual()
        with self.port.native(self.p, self.run, "read") as service:
            initial = service.read(self.run, first_receipt["validation_id"])[0]["grammar"]["elements"]
            initial = [e for e in initial if e["role"] == "data_series"][0]["payload"]["values"]
        run = self.admit_other(("Chart B x A y B: C 4; D 6.",), "changed")
        self.assertTrue(self.complete(run)["slice_complete"])
        second, second_receipt = self.visual(run)
        with self.port.native(self.p, run, "read") as service:
            changed = service.read(run, second_receipt["validation_id"])[0]["grammar"]["elements"]
            changed = [e for e in changed if e["role"] == "data_series"][0]["payload"]["values"]
        self.assertEqual([r["y"] for r in initial], [2.0, 3.0])
        self.assertEqual([r["y"] for r in changed], [4.0, 6.0])
        self.assertNotEqual(first["fingerprint"], second["fingerprint"])
        self.assertNotEqual(first["source_id"], second["source_id"])

    def test_unsupported_math_prevents_director_and_visual_invocation(self):
        run = self.admit_other(("Compute the matrix inverse.",), "unsupported-math")
        result = self.complete(run)
        self.assertEqual(result["stages"]["MATH"], "BLOCKED")
        self.assertTrue(all(result["stages"][s] == "PENDING" for s in ("REASONING", "PEDAGOGY", "DIRECTOR", "VISUAL")))
        self.assertEqual(self.stack.calls, dict(generator=0, critic=0, annotator=0, reviewer=0))

    def test_director_provider_unavailable_prevents_visual(self):
        result = self.complete(providers=False)
        self.assertEqual(result["stages"]["DIRECTOR"], "BLOCKED")
        self.assertEqual(result["stages"]["VISUAL"], "PENDING")
        self.assertIsNone(result["visual"])


class CurrentInputTests(PreparedVisualFixture):
    def test_native_sync_has_exact_director_reference_and_review_boundary(self):
        ctx, records, _, candidate, director, _ = self.current_inputs()
        self.assertEqual(candidate.payload["director_ref"], asdict(director.to_ref()))
        self.assertEqual(candidate.payload["review_boundary"], "PLANNING_PREVIEW_ONLY")
        self.assertTrue(candidate.metadata["requires_review"])
        self.assertFalse(candidate.metadata["accepted"])
        self.assertFalse(candidate.metadata["release_ready"])
        self.assertEqual(len(records), len(ctx.intents))

    def test_intents_derive_from_actual_narration_evidence_and_objectives(self):
        _, records, _, candidate, director, _ = self.current_inputs()
        with self.port.native(self.p, self.run, "read") as service:
            with native_runtime(service, self.run, None) as assembly:
                consumers = DirectorConsumers(assembly.io, DirectorRevisionStore(assembly.idempotency))
                _, execution = consumers._director(director.to_ref())
                utterances = {u.utterance_id: u for u in execution.snapshot.utterances}
                for cue in candidate.payload["result"]["cues"]:
                    binding = cue["binding"]
                    anchor = binding["anchor"]
                    utterance = utterances[anchor["utterance_id"]]
                    self.assertLessEqual(set(binding["objective_ids"]), set(utterance.objective_ids))
                    self.assertLessEqual(set(binding["evidence_ids"]), set(utterance.evidence_ids))
        self.assertTrue(all(r["concept_ids"] and r["reasoning_refs"] for r in records))

    def test_current_output_does_not_satisfy_historical_pinned_packet(self):
        from bie.visual_intelligence.canonical_dir_codec import CanonicalDirSourceReceipt, decode_canonical_dir_packet
        with self.port.native(self.p, self.run, "read") as service:
            output, _ = service.verified_director(self.run, "local")
        receipt = CanonicalDirSourceReceipt("73840d86a78e5f31438e2a1bad34f3b2a8433eb9",
            "adf64727adaf2ec9dd92c8f1ea03e2df2b8d738c", 71, 59, 683, True)
        with self.assertRaises(Exception):
            decode_canonical_dir_packet(output.payload, receipt)

    def test_foreign_director_artifact_rejected(self):
        with self.port.native(self.p, self.run, "read") as service:
            aid, _ = service.stage_ref(self.run, "DIRECTOR")
            with closing(sqlite3.connect(service.persistence.path)) as db:
                with db:
                    db.execute("UPDATE artifact_records SET run_id='foreign' WHERE artifact_id=?", (aid,))
        with self.assertRaises(Exception):
            self.step()

    def test_foreign_reasoning_artifact_rejected(self):
        with self.port.native(self.p, self.run, "read") as service:
            aid, _ = service.stage_ref(self.run, "REASONING")
            with closing(sqlite3.connect(service.persistence.path)) as db:
                with db:
                    db.execute("UPDATE artifact_records SET run_id='foreign' WHERE artifact_id=?", (aid,))
        with self.assertRaises(Exception):
            self.step()

    def test_tampered_director_rejected(self):
        self.tamper_stage("DIRECTOR")
        with self.assertRaises(Exception):
            self.step()

    def test_tampered_reasoning_rejected(self):
        self.tamper_stage("REASONING")
        with self.assertRaises(Exception):
            self.step()

    def test_source_bytes_tamper_rejected(self):
        self.tamper_stage("SOURCE")
        with self.assertRaises(Exception):
            self.step()

    def test_stale_director_revision_rejected(self):
        with self.port.native(self.p, self.run, "read") as service:
            with closing(sqlite3.connect(service.root / "director-state.sqlite3")) as db:
                with db:
                    db.execute("UPDATE director_revisions SET state='STALE' WHERE run_id=?", (self.run,))
        with self.assertRaises(Exception):
            self.step()

    def test_semantic_policy_blocker_prevents_visual_success(self):
        from bie.visual_intelligence.semantic_constraint_engine import Report, Violation
        report = Report(False, (Violation("declared_semantics", "source", "technical negative control"),),
            ("declared_semantics",), "a" * 64)
        with patch("bie.productization.visual_plan.semantic_policies", return_value=report):
            self.assert_failed_visual(self.step(), "visual_semantic_qa_blocked")

    def test_accessibility_failure_prevents_visual_success(self):
        from bie.visual_intelligence.contrast import evaluate_contrast
        def fail(intent, **kwargs):
            return evaluate_contrast(intent, foreground="#FFFFFF", background="#FFFFFF")
        with patch("bie.productization.visual_plan.evaluate_contrast", side_effect=fail):
            self.assert_failed_visual(self.step(), "visual_accessibility_blocked")

    def test_target_intent_conflict_rejected(self):
        changed = deepcopy(self.config)
        changed["visual"] = visual_config(target(profile_id="different-governed-target"))
        with self.assertRaises(Exception):
            self.port.admit(self.p, self.source["source_id"], "intent", producer_config=changed)

    def test_same_source_and_intent_replays_run_identity(self):
        result = self.port.admit(self.p, self.source["source_id"], "intent", producer_config=self.config)
        self.assertEqual(result["run_id"], self.run)
        self.assertEqual(result["stages"]["VISUAL"], "READY")
        self.assertEqual(self.stack.calls, dict(generator=0, critic=0, annotator=0, reviewer=0))

    def test_profile_scope_tamper_rejected(self):
        with self.port.native(self.p, self.run, "read") as service:
            with closing(sqlite3.connect(service.persistence.path)) as db:
                with db:
                    db.execute("DELETE FROM attempts WHERE run_id=? AND stage_id='VISUAL'", (self.run,))
                    db.execute("DELETE FROM stages WHERE run_id=? AND stage_id='VISUAL'", (self.run,))
        with self.assertRaises(Exception):
            self.port.status(self.p, self.run)


class CommittedVisualTests(PreparedVisualFixture):
    PREPARE_COMPLETE = True

    def replace_receipt_with_valid_cas(self, **changes):
        """Attacker-controlled durable row, with genuine recomputed CAS identity.

        This is stronger than damaged blob bytes: hash/record identity remain
        valid, so independent producer receipt validation must reject it.
        """
        _, receipt = self.visual()
        forged = deepcopy(receipt)
        forged.update(changes)
        with self.port.native(self.p, self.run, "worker") as service:
            current = service.persistence.load_run_state(self.run)["stages"]["VISUAL"]["attempts"][-1]
            old = service.record(self.run, current["evidence_refs"][0])
            aid = service.put(self.run, "VISUAL", "producer.evidence", forged, old.parent_artifact_ids, True)
            self.assertNotEqual(aid, old.artifact_id)
            self.assertEqual(service.read(self.run, aid), forged)
            with closing(sqlite3.connect(service.persistence.path)) as db:
                with db:
                    db.execute("UPDATE attempts SET evidence_refs_json=? WHERE run_id=? AND stage_id='VISUAL' AND attempt=?",
                               (json.dumps([aid]), self.run, current["attempt"]))
        with self.assertRaises(ProducerError):
            self.port.status(self.p, self.run)

    def test_valid_cas_receipt_wrong_run_rejected(self):
        self.replace_receipt_with_valid_cas(run_id="foreign-run")

    def test_valid_cas_receipt_wrong_stage_rejected(self):
        self.replace_receipt_with_valid_cas(stage="DIRECTOR")

    def test_valid_cas_receipt_wrong_schema_rejected(self):
        self.replace_receipt_with_valid_cas(schema="bie.producer.stage-evidence/2")

    def test_valid_cas_receipt_review_cannot_be_removed(self):
        self.replace_receipt_with_valid_cas(requires_review=False)

    def test_valid_cas_receipt_cannot_claim_acceptance(self):
        self.replace_receipt_with_valid_cas(accepted=True)

    def test_valid_cas_receipt_cannot_claim_release_readiness(self):
        self.replace_receipt_with_valid_cas(release_ready=True)

    def test_valid_cas_receipt_cannot_claim_product_acceptance(self):
        self.replace_receipt_with_valid_cas(product_accepted=True)

    def test_valid_cas_receipt_cannot_claim_academic_evidence(self):
        self.replace_receipt_with_valid_cas(evidence_kind="ACADEMIC_ACCEPTANCE")

    def test_valid_cas_receipt_cannot_falsely_claim_historical_dir_runtime(self):
        self.replace_receipt_with_valid_cas(historical_dir_runtime_claimed=True)

    def test_valid_cas_receipt_cannot_falsely_claim_historical_rep_runtime(self):
        self.replace_receipt_with_valid_cas(historical_rep_archive_runtime_claimed=True)

    def test_valid_cas_receipt_invented_intent_count_rejected(self):
        self.replace_receipt_with_valid_cas(visual_intent_count=99)

    def test_valid_cas_receipt_invented_abstention_count_rejected(self):
        self.replace_receipt_with_valid_cas(abstention_count=99)

    def test_valid_cas_receipt_invented_internal_stage_count_rejected(self):
        self.replace_receipt_with_valid_cas(internal_stage_count=9)

    def test_valid_cas_receipt_stale_fencing_epoch_rejected(self):
        self.replace_receipt_with_valid_cas(fencing_epoch=999)

    def test_valid_cas_receipt_extra_private_source_field_rejected(self):
        self.replace_receipt_with_valid_cas(private_source_text=CHART)

    def test_committed_replay_has_no_model_calls(self):
        before = self.port.status(self.p, self.run)
        self.assertEqual(self.step(), before)
        self.assertEqual(self.stack.calls, dict(generator=0, critic=0, annotator=0, reviewer=0))

    def test_native_animation_handoff_compatibility_without_animation_execution(self):
        _, receipt = self.visual()
        with self.port.native(self.p, self.run, "read") as service:
            raw = service.read(self.run, receipt["handoff_id"])
            adopted = adopt_visual_handoff(raw, 1, receipt["plan_fingerprint"])
            self.assertEqual(adopted.plan_fingerprint, receipt["plan_fingerprint"])
            self.assertFalse(adopted.accepted)
        self.assertEqual(self.port.status(self.p, self.run)["downstream"]["ANIMATION"], "NOT_RUN")

    def test_visual_plan_fingerprint_tamper_rejected(self):
        plan, _ = self.visual()
        plan["fingerprint"] = "f" * 64
        with self.assertRaises(Exception):
            VisualPlan.from_dict(plan)

    def test_visual_plan_cannot_self_accept(self):
        plan, _ = self.visual()
        plan["accepted"] = True
        with self.assertRaises(Exception):
            VisualPlan.from_dict(plan)

    def test_plan_cas_tamper_rejected_on_reopen(self):
        self.tamper_stage("VISUAL")
        with self.assertRaises(Exception):
            self.port.status(self.p, self.run)

    def test_sync_candidate_cas_tamper_rejected_on_reopen(self):
        _, receipt = self.visual()
        with self.port.native(self.p, self.run, "read") as service:
            row = service.record(self.run, receipt["sync_ref"]["artifact_id"])
            service.cas._path(row.blob_digest).write_bytes(b"deliberate-sync-tamper")
        with self.assertRaises(Exception):
            self.port.status(self.p, self.run)

    def test_internal_stage_cas_tamper_rejected_on_reopen(self):
        _, receipt = self.visual()
        with self.port.native(self.p, self.run, "read") as service:
            row = service.record(self.run, receipt["internal_record_ids"][2])
            service.cas._path(row.blob_digest).write_bytes(b"deliberate-internal-tamper")
        with self.assertRaises(Exception):
            self.port.status(self.p, self.run)

    def test_currentness_change_invalidates_committed_visual(self):
        with self.port.native(self.p, self.run, "read") as service:
            with closing(sqlite3.connect(service.root / "director-state.sqlite3")) as db:
                with db:
                    db.execute("UPDATE director_revisions SET state='STALE' WHERE run_id=?", (self.run,))
        with self.assertRaises(Exception):
            self.port.status(self.p, self.run)

    def test_safe_projection_and_receipt_exclude_private_source(self):
        status = self.port.status(self.p, self.run)
        _, receipt = self.visual()
        decoded = list(decoded_strings(status)) + list(decoded_strings(receipt))
        for fragment in (CHART, self.token, str(self.root), "What does the cited source state?", "protocol interpretation"):
            self.assertTrue(all(fragment not in value for value in decoded))
        self.assertFalse(status["product_accepted"])
        self.assertFalse(status["visual"]["accepted"])

    def test_private_intermediates_share_existing_cas_and_run_store(self):
        _, receipt = self.visual()
        with self.port.native(self.p, self.run, "read") as service:
            for aid in (receipt["current_inputs_id"], receipt["validation_id"], receipt["handoff_id"],
                        receipt["output_artifact_id"], *receipt["internal_record_ids"]):
                row = service.record(self.run, aid)
                self.assertEqual(row.run_id, self.run)
                self.assertEqual(row.metadata["privacy"], "PRIVATE")
            self.assertEqual(service.persistence.path.name, "runs.sqlite3")
            self.assertEqual(service.queue.path.name, "queue.sqlite3")


class SourceDeclarationTests(unittest.TestCase):
    def test_keyword_alone_cannot_produce_semantics(self):
        self.assertIsNone(parse_declaration("A chart could clarify this concept."))

    def test_partial_chart_without_axis_semantics_is_not_admitted(self):
        self.assertIsNone(parse_declaration("Chart: C 2; D 3."))

    def test_invalid_or_duplicate_sample_labels_are_not_admitted(self):
        self.assertIsNone(parse_declaration("Chart B x A y B: C 2; C 3."))

    def test_equation_is_not_falsely_recast_as_chart(self):
        self.assertIsNone(parse_declaration("2 + 2 = 4"))

    def test_timeline_retains_source_and_chronological_order_distinctly(self):
        parsed = parse_declaration("Timeline: A at 1820; B at 1810.")
        self.assertEqual(parsed["semantic_obligations"]["source_order"], ["A", "B"])
        self.assertEqual(parsed["semantic_obligations"]["chronological_order"], ["B", "A"])

    def test_uncertain_date_is_not_promoted_to_exact(self):
        parsed = parse_declaration("Timeline: A at about 1810; B at 1820.")
        event = parsed["grammar_inputs"]["events"][0]
        self.assertTrue(event["uncertain"])
        self.assertEqual(event["time_label"], "about 1810")

    def test_cellular_containment_is_retained_even_when_not_plannable(self):
        parsed = parse_declaration("Cell: A C; B R in A.")
        self.assertEqual(parsed["grammar_inputs"]["components"][1]["parent_id"], "A")


class CodeIdentityScopeTests(unittest.TestCase):
    """Pure source hashing only; no artifacts, native runtime or budget mocks."""

    @staticmethod
    @contextmanager
    def fake_native(unused, principal, run, permission, **options):
        yield object()

    def test_hashes_are_memoized_only_within_each_control_plane_operation(self):
        from apps.operator.knowledge_producer import KnowledgeProducerControlPlane
        from bie.productization import visual_contract as contract
        port = object.__new__(VisualProducerControlPlane)
        with patch.object(KnowledgeProducerControlPlane, "native", self.fake_native), \
                patch.object(contract, "sha", wraps=contract.sha) as hashed:
            with port.native(None, "run", "read"):
                first = contract.engine_identity()
                one_read = hashed.call_count
                self.assertGreater(one_read, 0)
                self.assertEqual(contract.engine_identity(), first)
                self.assertEqual(hashed.call_count, one_read)
            with port.native(None, "run", "read"):
                self.assertEqual(contract.engine_identity(), first)
                self.assertEqual(hashed.call_count, 2 * one_read)

    def test_memoized_code_identity_is_returned_as_defensive_copy(self):
        from bie.productization import visual_contract as contract
        with contract.code_identity_scope():
            identity = contract.engine_identity()
            expected = dict(identity)
            identity[next(iter(identity))] = "forged-code-hash"
            identity["foreign-module"] = "forged-code-hash"
            self.assertEqual(contract.engine_identity(), expected)

    def test_ack_hook_refreshes_hashes_before_full_inherited_status_validation(self):
        from bie.productization import visual_contract as contract
        service = object.__new__(VisualProducerService)
        observations = []
        with contract.code_identity_scope(), patch.object(contract, "sha", wraps=contract.sha) as hashed:
            expected = contract.engine_identity()
            before = hashed.call_count
            def status(unused, run, tenant):
                observations.append((run, tenant, hashed.call_count, contract.engine_identity()))
                return dict(technical=True)
            with patch.object(VisualProducerService, "status", autospec=True, side_effect=status) as validated:
                service.verify_terminal_for_ack("run", "local")
                validated.assert_called_once_with(service, "run", "local")
            self.assertEqual(observations, [("run", "local", 2 * before, expected)])
            self.assertEqual(hashed.call_count, 2 * before)

    def test_control_plane_scope_resets_after_exception(self):
        from apps.operator.knowledge_producer import KnowledgeProducerControlPlane
        from bie.productization import visual_contract as contract
        port = object.__new__(VisualProducerControlPlane)
        with patch.object(KnowledgeProducerControlPlane, "native", self.fake_native), \
                patch.object(contract, "sha", wraps=contract.sha) as hashed:
            with self.assertRaisesRegex(RuntimeError, "technical interruption"):
                with port.native(None, "run", "read"):
                    expected = contract.engine_identity()
                    before = hashed.call_count
                    raise RuntimeError("technical interruption")
            self.assertEqual(contract.engine_identity(), expected)
            self.assertEqual(hashed.call_count, 2 * before)

    def test_direct_engine_identity_calls_remain_uncached(self):
        from bie.productization import visual_contract as contract
        with patch.object(contract, "sha", wraps=contract.sha) as hashed:
            first = contract.engine_identity()
            before = hashed.call_count
            self.assertGreater(before, 0)
            self.assertEqual(contract.engine_identity(), first)
            self.assertEqual(hashed.call_count, 2 * before)


class NativeIntentNegativeTests(PreparedVisualFixture):
    def actual_inputs(self):
        with self.port.native(self.p, self.run, "read") as service:
            output, _ = service.verified_director(self.run, self.p.tenant)
            request, _, _ = service.request(self.run, self.p.tenant)
            with native_runtime(service, self.run, None) as runtime:
                _, execution = DirectorConsumers(runtime.io,
                    DirectorRevisionStore(runtime.idempotency))._director(output.to_ref())
                inputs = load_director_inputs(runtime.io, request.reasoning_ref, request.pedagogy_ref,
                    lesson_id=request.lesson_id, title=request.title, language=request.language, run_id=self.run)
        return inputs, execution

    def sync_with_binding(self, **changes):
        inputs, execution = self.actual_inputs()
        typed, _, _ = derive_intents(inputs, execution)
        edited = replace(typed[0], binding=replace(typed[0].binding, **changes))
        ctx = build_sync_context(execution.speech, execution.pauses, execution.emphasis, execution.timeline)
        return sync_visual_intents(ctx, (edited,))

    def test_fixture_like_inputs_rejected(self):
        with self.assertRaises(ProducerError):
            derive_intents({}, {})

    def test_fabricated_typed_target_rejected_by_independent_derivation(self):
        inputs, execution = self.actual_inputs()
        typed, records, _ = derive_intents(inputs, execution)
        forged = replace(typed[0], binding=replace(typed[0].binding, target_id="foreign-target"))
        with self.assertRaises(ProducerError):
            validate_derived(inputs, execution, (forged,), records)

    def test_invented_source_semantics_rejected_by_independent_derivation(self):
        inputs, execution = self.actual_inputs()
        typed, records, _ = derive_intents(inputs, execution)
        records[0]["grammar_inputs"]["series"][0]["values"][0]["y"] = 999.0
        with self.assertRaises(ProducerError):
            validate_derived(inputs, execution, typed, records)

    def test_foreign_evidence_outside_narration_rejected(self):
        with self.assertRaises(Exception):
            self.sync_with_binding(evidence_ids=("foreign-evidence",))

    def test_foreign_objective_outside_narration_rejected(self):
        with self.assertRaises(Exception):
            self.sync_with_binding(objective_ids=("foreign-objective",))

    def test_foreign_narration_anchor_rejected(self):
        inputs, execution = self.actual_inputs()
        typed, _, _ = derive_intents(inputs, execution)
        with self.assertRaises(Exception):
            self.sync_with_binding(anchor=replace(typed[0].binding.anchor, utterance_id="foreign-utterance"))

    def test_stale_narration_fingerprint_rejected(self):
        inputs, execution = self.actual_inputs()
        typed, _, _ = derive_intents(inputs, execution)
        with self.assertRaises(Exception):
            self.sync_with_binding(anchor=replace(typed[0].binding.anchor, utterance_fingerprint="a" * 64))

    def test_word_span_outside_actual_narration_rejected(self):
        inputs, execution = self.actual_inputs()
        typed, _, _ = derive_intents(inputs, execution)
        with self.assertRaises(Exception):
            self.sync_with_binding(anchor=replace(typed[0].binding.anchor, end_word=9999))

    def test_unsupported_sceneir_element_kind_rejected(self):
        inputs, execution = self.actual_inputs()
        typed, _, _ = derive_intents(inputs, execution)
        ctx = build_sync_context(execution.speech, execution.pauses, execution.emphasis, execution.timeline)
        with self.assertRaises(Exception):
            sync_visual_intents(ctx, (replace(typed[0], kind="invented-visual"),))

    def test_timing_request_outside_narration_cannot_be_silently_clamped(self):
        inputs, execution = self.actual_inputs()
        typed, _, _ = derive_intents(inputs, execution)
        ctx = build_sync_context(execution.speech, execution.pauses, execution.emphasis, execution.timeline)
        plan = sync_visual_intents(ctx, (replace(typed[0], lead_ms=999999),))
        self.assertEqual(plan.status, "BLOCKED")
        self.assertIn("LEAD_BEFORE_SCENE", {issue.code for issue in plan.issues})

    def test_map_semantics_not_supported_by_current_bridge_are_rejected(self):
        ctx, records, _, _, _, _ = self.current_inputs()
        records[0]["semantic_kind"] = "map"
        with self.assertRaisesRegex(ProducerError, "visual_representation_unsupported"):
            build_current_plan(ctx, records, target(), run_id=self.run, revision=1)

    def test_sampled_chart_missing_axis_semantics_blocked_by_native_rep(self):
        ctx, records, _, _, _, _ = self.current_inputs()
        records[0]["rep_parameters"]["axis_semantics"] = False
        with self.assertRaises(ProducerError):
            build_current_plan(ctx, records, target(), run_id=self.run, revision=1)

    def test_sampled_values_cannot_be_promoted_to_exact_analytic_curve(self):
        ctx, records, _, _, _, _ = self.current_inputs()
        records[0]["rep_parameters"]["exact_curve_claim"] = True
        with self.assertRaises(ProducerError):
            build_current_plan(ctx, records, target(), run_id=self.run, revision=1)

    def test_native_grammar_cannot_change_source_sample_values(self):
        ctx, records, _, _, _, _ = self.current_inputs()
        records[0]["grammar_inputs"]["series"][0]["values"][0]["y"] = 999.0
        with self.assertRaisesRegex(ProducerError, "visual_source_semantics_changed"):
            build_current_plan(ctx, records, target(), run_id=self.run, revision=1)

    def test_native_grammar_cannot_change_source_axis_label(self):
        ctx, records, _, _, _, _ = self.current_inputs()
        records[0]["grammar_inputs"]["x_label"] = "foreign-axis"
        with self.assertRaisesRegex(ProducerError, "visual_source_semantics_changed"):
            build_current_plan(ctx, records, target(), run_id=self.run, revision=1)

    def test_target_without_2d_capability_cannot_unlock_plan(self):
        ctx, records, _, _, _, _ = self.current_inputs()
        with self.assertRaises(ProducerError):
            build_current_plan(ctx, records, target(capabilities=["math_text"]), run_id=self.run, revision=1)

    def test_actual_source_complexity_cannot_exceed_explicit_target_budget(self):
        from bie.productization.visual_plan import MAX_ELEMENTS
        ctx, records, _, _, _, _ = self.current_inputs()
        expected = len(records[0]["semantic_obligations"]["source_items"]) / MAX_ELEMENTS
        _, _, receipts = build_current_plan(ctx, records, target(), run_id=self.run, revision=1)
        rep = receipts[0]["representation"]
        self.assertEqual(rep["dimension"]["payload"]["complexity"], expected)
        self.assertEqual(rep["composition"]["complexity"], expected)
        with self.assertRaisesRegex(ProducerError, "visual_target_complexity_exceeded"):
            build_current_plan(ctx, records, target(max_complexity=expected / 2),
                               run_id=self.run, revision=1)


if __name__ == "__main__":
    unittest.main()
