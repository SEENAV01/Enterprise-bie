"""Exact amendment and unversioned compatibility; no historical assertions edited."""
from copy import deepcopy
from dataclasses import asdict
from hashlib import sha256
from importlib.machinery import SourceFileLoader
from importlib.util import spec_from_loader, module_from_spec
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

from scripts import compiler_motion_source_amendment as audit
from bie.compiler.animation_behavior import motion_contract,motion_state
from bie.compiler.animation_track_compiler import compile_animation_track
from bie.compiler.reduced_motion import resolve_reduced_motion
from tests.compiler.h2_test_support import track
from tests.compiler.h3_test_support import TARGET,scene,move,variant

ROOT=Path(__file__).resolve().parents[2]


def before(name):
    key="bie.compiler._m1_original_"+name
    loader=SourceFileLoader(key,str(ROOT/"docs/productization/task036-motion-amendment"/(name+".py.before")))
    spec=spec_from_loader(key,loader);module=module_from_spec(spec);sys.modules[key]=module;loader.exec_module(module)
    return module


class UnversionedCompatibility(unittest.TestCase):
    def test_unversioned_motion_contracts_and_all_frames_identical(self):
        old=before("animation_behavior")
        inputs=[track(a,p) for a,p in [("enter",{}),("exit",{}),("reveal",{"direction":"right"}),
            ("emphasize",{"peak_scale":1.2}),("transform",{"from":{"scale":1},"to":{"scale":1.2}}),
            ("path_follow",{"coordinate_space":"pixels","points":[[0,0],[10,20]]})]]
        for t in inputs:
            a,b=old.motion_contract(t),motion_contract(t)
            self.assertEqual(asdict(a),asdict(b))
            for frame in range(49):self.assertEqual(old.motion_state(a,frame,24),motion_state(b,frame,24))

    def test_unversioned_emission_bytes_identical(self):
        old=before("animation_track_compiler")
        for action in ("enter","exit","reveal","emphasize"):
            self.assertEqual(asdict(old.compile_animation_track(track(action))),asdict(compile_animation_track(track(action))))

    def test_unversioned_standard_and_reduced_receipts_identical(self):
        old=before("reduced_motion")
        raw=variant(move())
        for preference in ("standard","reduced"):
            self.assertEqual(old.resolve_reduced_motion(raw,TARGET,preference),resolve_reduced_motion(raw,TARGET,preference))

    def test_unversioned_opaque_metadata_does_not_select_new_behavior(self):
        old=before("reduced_motion")
        raw=variant(move());raw["metadata"]["producer_motion"]={"legacy_annotation":"opaque"}
        self.assertEqual(old.resolve_reduced_motion(raw,TARGET,"reduced"),resolve_reduced_motion(raw,TARGET,"reduced"))

    def test_unversioned_rejection_codes_conditions_identical(self):
        old=before("reduced_motion")
        values=[move(),variant(move())]
        values[1]["metadata"]["compiler_h3"]["reduced_motion_variants"]["variant:e0"]["track_replacements"]["h3move"]={"action":"reveal","parameters":{}}
        for raw in values:
            outcomes=[]
            for function in (old.resolve_reduced_motion,resolve_reduced_motion):
                try:function(raw,TARGET,"reduced")
                except ValueError as e:outcomes.append((type(e).__name__,str(e)))
            self.assertEqual(len(outcomes),2);self.assertEqual(*outcomes)

    def test_unknown_legacy_keys_still_rejected(self):
        old=before("animation_behavior")
        for function in (old.motion_contract,motion_contract):
            for key in ("scale_allowed","reduced_safe","accepted","foreign"):
                with self.assertRaisesRegex(ValueError,"ANIMATION_PARAMETER_UNCONSUMED"):
                    function(track("emphasize",{key:False}))


class ExactMotionAmendment(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        shutil.copytree(ROOT/"bie/compiler",self.root/"bie/compiler",ignore=shutil.ignore_patterns("__pycache__"))
        shutil.copytree(ROOT/"docs/productization/task036-motion-amendment",self.root/"docs/productization/task036-motion-amendment")
        (self.root/"manifests").mkdir()
        shutil.copyfile(ROOT/"manifests"/audit.MANIFEST,self.root/"manifests"/audit.MANIFEST)
        # Preserve every original assertion while exercising the exact current
        # follow-on helper inventory through its sealed amendment chain.
        for name in ('task036-capture-observation-amendment','task036-media-observation-amendment','task036-media-thread-amendment'):
            shutil.copytree(ROOT/'docs/productization'/name,self.root/'docs/productization'/name)
        (self.root/'scripts').mkdir()
        for name in ('compiler_cache_source_amendment.py','compiler_capture_observation_amendment.py',
                     'compiler_media_observation_amendment.py','compiler_motion_source_amendment.py'):
            shutil.copyfile(ROOT/'scripts'/name,self.root/'scripts'/name)

    def tearDown(self):self.tmp.cleanup()

    def test_exact_original_and_new_bytes_validate(self):
        sealed,doc=audit.validate(self.root)
        self.assertEqual(len(doc["replacements"]),4)
        self.assertEqual(len(doc["additions"]),3)
        self.assertFalse(doc["product_accepted"])

    def test_every_changed_native_file_tamper_rejected(self):
        for path in sorted(audit.TARGETS|audit.ADDITIONS):
            file=self.root/path;raw=file.read_bytes();file.write_bytes(raw+b"\n# tamper\n")
            try:
                with self.subTest(path=path),self.assertRaises(ValueError):audit.validate(self.root)
            finally:file.write_bytes(raw)

    def test_each_historical_preimage_tamper_rejected(self):
        for file in (self.root/"docs/productization/task036-motion-amendment").glob("*.before"):
            raw=file.read_bytes();file.write_bytes(raw+b"#tamper")
            try:
                with self.subTest(path=file.name),self.assertRaises(ValueError):audit.validate(self.root)
            finally:file.write_bytes(raw)

    def test_recomputed_replacement_hash_cannot_self_approve(self):
        file=self.root/next(iter(audit.TARGETS));file.write_bytes(file.read_bytes()+b"# changed\n")
        doc=json.loads((self.root/audit.DOCUMENT).read_text())
        for r in doc["replacements"]:
            if r["path"]==file.relative_to(self.root).as_posix():
                r["active_sha256"]=sha256(file.read_bytes()).hexdigest();r["active_bytes"]=file.stat().st_size
        (self.root/audit.DOCUMENT).write_text(json.dumps(doc),encoding="utf-8")
        with self.assertRaisesRegex(ValueError,"DOCUMENT_IDENTITY"):audit.validate(self.root)

    def test_unlisted_compiler_path_rejected(self):
        (self.root/"bie/compiler/unapproved.py").write_text("# not authorized\n")
        with self.assertRaisesRegex(ValueError,"UNEXPECTED_COMPILER_PATH"):audit.validate(self.root)

    def test_duplicate_ambiguous_or_wildcard_document_rejected(self):
        path=self.root/audit.DOCUMENT;raw=path.read_bytes()
        for value in (raw[:-2]+b',"replacements":[]}\n',b'{"paths":["bie/compiler/**"]}\n'):
            path.write_bytes(value)
            with self.assertRaises(ValueError):audit.validate(self.root)

    def test_original_ledger_cannot_be_rewritten(self):
        file=self.root/"manifests"/audit.MANIFEST;file.write_bytes(file.read_bytes()+b" ")
        with self.assertRaisesRegex(ValueError,"ORIGINAL_MANIFEST"):audit.validate(self.root)


if __name__=="__main__":unittest.main()
