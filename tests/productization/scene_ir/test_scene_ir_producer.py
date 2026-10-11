"""Actual persisted upstream journeys plus independent native conservation checks."""
from copy import deepcopy
from dataclasses import asdict, replace
import gc
from pathlib import Path
import secrets
import shutil
import sys
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[3]
for folder in (ROOT, ROOT / "tests/productization/document_intelligence",
               ROOT / "tests/productization/director", ROOT / "tests/productization/visual",
               ROOT / "tests/productization/animation"):
    sys.path.insert(0, str(folder))
from test_animation_producer import config as animation_configuration
from test_visual_producer import pdf, CHART, TIMELINE, CELL
from protocol_support import make_stack
from apps.operator.contracts import Credentials, Principal
from apps.operator.service import Service
from apps.operator.scene_ir_producer import SceneIRProducerControlPlane
from bie.productization.scene_ir_contract import PROFILE, profile_config, scene_ir_config, strict_document
from bie.productization.scene_ir_slice import STAGES
from bie.productization.scene_ir_plan import build_current_scene, scene_scope
from bie.productization.scene_ir_catalog import verify_inventory
from bie.productization.contracts import ProducerError, canonical
from bie.productization.director_storage import native_runtime
from bie.director.director_consumers import DirectorConsumers
from bie.director.director_revisions import DirectorRevisionStore


def configuration(stack):
    current = animation_configuration(stack)
    return profile_config(director=current["director"], visual=current["visual"],
        animation=current["animation"], scene_ir=scene_ir_config())


class SceneFixture(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        prepared = getattr(type(self), "_prepared", None)
        if prepared is not None:
            shutil.copytree(prepared.root, self.root, dirs_exist_ok=True)
        self.credentials = Credentials()
        self.p = Principal("task036-test", "local", frozenset({"read", "source", "create", "worker",
            "control", "admin_recover"}), time.time() + 900)
        self.credentials.grant(secrets.token_urlsafe(40), self.p)
        self.operator = Service(self.root, self.credentials)
        self.stack = make_stack()
        self.config = configuration(self.stack)
        self.port = SceneIRProducerControlPlane(self.operator, enabled_profiles={PROFILE})
        if prepared is not None:
            self.run = prepared.run
            self.source = self.operator.source(self.p, prepared.source["source_id"])
            self.config = deepcopy(prepared.config)

    def tearDown(self):
        gc.collect()
        self.tmp.cleanup()

    def admit(self, lines=(CHART,), key="scene"):
        self.source = self.operator.import_pdf(self.p, pdf(lines))
        self.run = self.port.admit(self.p, self.source["source_id"], key, producer_config=self.config)["run_id"]
        return self.run

    def step(self):
        return self.port.work_once(self.p, self.run, director_stack=self.stack)

    def upstream(self):
        for _ in range(10):
            result = self.step()
            if any(s in ("FAILED", "BLOCKED") for s in result["stages"].values()):
                break
        self.assertEqual(result["stages"]["ANIMATION"], "SUCCEEDED", result.get("safe_diagnostics"))
        return result

    def complete(self, lines=(CHART,)):
        self.admit(lines)
        self.upstream()
        result = self.step()
        self.assertEqual(result["stages"]["SCENE_IR"], "SUCCEEDED", result.get("safe_diagnostics"))
        return result


class PreparedSceneFixture(SceneFixture):
    """Closed actual ten-stage bytes, fresh Scene IR execution per control.

    This unit-test efficiency mechanism is NOT the required fresh eleven-stage
    child/restart smoke. That smoke creates every predecessor in its first child.
    """
    @classmethod
    def setUpClass(cls):
        fixture = SceneFixture()
        try:
            fixture.setUp()
            fixture.admit()
            fixture.upstream()
        except BaseException:
            if hasattr(fixture, "tmp"):
                fixture.tearDown()
            raise
        cls._prepared = fixture

    @classmethod
    def tearDownClass(cls):
        cls._prepared.tearDown()
        del cls._prepared


class RealSourceCases(SceneFixture):
    def check_family(self, line):
        result = self.complete((line,))
        self.assertEqual(len(result["stages"]), 11)
        self.assertTrue(all(s == "SUCCEEDED" for s in result["stages"].values()))
        self.assertTrue(all(s == "NOT_RUN" for s in result["downstream"].values()))
        with self.port.native(self.p, self.run, "read") as service:
            document, receipt = service.verified_scene_ir(self.run, self.p.tenant)
            self.assertEqual(receipt["input_artifact_ids"], [service.stage_ref(self.run, s)[0]
                for s in ("VISUAL", "ANIMATION", "DIRECTOR")])
            self.assertEqual(document["schema_version"], "1.0.0")
            self.assertTrue(document["review_required"])
            self.assertFalse(document["accepted"])
            self.assertTrue(receipt["requires_review"])
            self.assertFalse(receipt["release_ready"])
            self.assertFalse(receipt["audio_complete"])
            self.assertTrue(receipt["audio_reconciliation_open"])
            self.assertEqual(receipt["native_validator_count"], 7)
            self.assertEqual(strict_document(canonical(document)).to_dict(), document)
            state = service.persistence.load_run_state(self.run)["stages"]["SCENE_IR"]["attempts"][-1]
            self.assertEqual(state["input_artifact_refs"], receipt["input_artifact_ids"])
        return document

    def test_quantitative_real_source_and_static_axes(self):
        doc = self.check_family(CHART)
        charts = [e for e in doc["elements"] if e["element_type"] == "chart"]
        self.assertEqual(charts[0]["props"]["values"], [2.0, 3.0])
        self.assertEqual(charts[0]["props"]["categories"], ["C", "D"])
        self.assertEqual({e["element_type"] for e in doc["elements"]}, {"shape", "text", "chart"})
        self.assertEqual(len(doc["tracks"]), 1)

    def test_chronology_real_source_and_order(self):
        doc = self.check_family(TIMELINE)
        labels = [e["props"]["nodes"][0]["label"] for e in doc["elements"] if e["element_type"] == "diagram"]
        self.assertEqual(labels, ["A | 1810", "B | 1820"])
        self.assertEqual(len(doc["tracks"]), 2)

    def test_cellular_real_source_no_geometry_motion(self):
        doc = self.check_family(CELL)
        self.assertEqual({t["action"] for t in doc["tracks"]}, {"emphasize"})
        self.assertTrue(all(t["parameters"]["original"]["parameters"]["scale_allowed"] is False for t in doc["tracks"]))

    def test_multiple_complete_scenes_block_not_first_scene(self):
        self.admit((CHART, CELL))
        for _ in range(10):
            result = self.step()
            if result["stages"]["ANIMATION"] in ("FAILED", "BLOCKED"):
                break
        self.assertEqual(result["safe_diagnostics"], {"ANIMATION": ["animation_multiscene_timing_contract_required"]})
        self.assertEqual(result["stages"]["SCENE_IR"], "PENDING")
        self.assertIsNone(result["scene_ir"])
        self.assertFalse(result["slice_complete"])
        # Independently exercise Task036's complete-execution admission using
        # that actual persisted Director, not a fake second scene or first slice.
        with self.port.native(self.p, self.run, "read") as service:
            with native_runtime(service, self.run, None) as runtime:
                ref, _ = service.stage_ref(self.run, "DIRECTOR")
                _, execution = DirectorConsumers(runtime.io, DirectorRevisionStore(runtime.idempotency))._director(
                    runtime.io.load(ref).to_ref())
                with self.assertRaisesRegex(ProducerError, "scene_ir_multiple_scenes_unsupported"):
                    scene_scope(execution, [])


if __name__ == "__main__":
    unittest.main()
