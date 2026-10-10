"""Failure-observability contracts, NOT actual browser/frame/render proof.

Node fixtures explicitly substitute renderer packages only for call plumbing.
Pure Python reader functions are extracted verbatim from their canonical source;
this does not pretend the Linux-only painter was imported/executed on Windows.
The mandatory hosted matrix independently executes the real canonical consumer.
"""
import ast
from copy import deepcopy
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
from types import SimpleNamespace
import unittest

from bie.compiler.artifact_hashing import canonical_json
from tests.compiler import m1_safe_paint_diagnostics as safe

ROOT = Path(__file__).resolve().parents[2]
CONTROLLER = ROOT / "bie/compiler/qa_support/remotion_raster_capture.cjs"
BEFORE = ROOT / "docs/productization/task036-capture-observation-amendment/remotion_raster_capture.cjs.before"
MANIFEST = "a" * 64


def pure_native_reader():
    tree = ast.parse((ROOT / "bie/compiler/real_paint.py").read_text())
    names = {"CAPTURE_DIAGNOSTIC_SCHEMA", "CAPTURE_DIAGNOSTIC_PHASES", "CAPTURE_DIAGNOSTIC_GUARDS"}
    methods = {"validate_capture_failure_observation", "_retain_capture_failure_observation"}
    selected = [n for n in tree.body if
        (isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id in names for t in n.targets)) or
        (isinstance(n, ast.FunctionDef) and n.name in methods)]
    assert len(selected) == 5
    namespace = {"Path": Path, "json": json, "canonical_json": canonical_json}
    exec(compile(ast.Module(selected, type_ignores=[]), "canonical_pure_capture_reader", "exec"), namespace)
    return SimpleNamespace(validate=namespace["validate_capture_failure_observation"],
                           retain=namespace["_retain_capture_failure_observation"])


def receipt():
    return {"schema": "bie.capture-controller-failure/1", "phase": "MEASUREMENT_CHECK",
        "guard_code": "CAPTURE_DOM_NONDETERMINISM", "frame": 0, "shot_kind": "FULL",
        "target_index": -1, "frame_count": 2, "manifest_sha256": MANIFEST, "accepted": False}


class CaptureSafeReader(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.capture = self.root / "capture"
        self.capture.mkdir()
        self.out = self.root / "paint-standard"
        self.out.mkdir()
        self.file = self.capture / "CAPTURE_PROCESS_DIAGNOSTIC.json"
        self.native = pure_native_reader()

    def observe(self):
        return safe.capture_controller_observation(self.root, preference="standard", manifest_sha256=MANIFEST, frame_count=2)

    def put(self, value):
        self.file.write_text(json.dumps(value), encoding="utf-8")

    def retain(self):
        self.native.retain(self.capture, self.out, MANIFEST)

    def test_valid_observed_static_guard_retained(self):
        self.put(receipt()); self.retain()
        result = self.observe()
        self.assertTrue(safe.is_safe_capture_observation(result))
        self.assertEqual(result["receipt_state"], "VALID")
        self.assertEqual(result["guard_code"], "CAPTURE_DOM_NONDETERMINISM")
        self.assertFalse(result["render_passed"])

    def test_unknown_library_cause_remains_none_recorded(self):
        value = receipt(); value.update(phase="RENDER_STILL", guard_code="NONE_RECORDED")
        self.put(value); self.retain()
        self.assertEqual(self.observe()["guard_code"], "NONE_RECORDED")
        self.assertFalse(self.observe()["render_passed"])

    def test_absence_does_not_imply_success_or_zero(self):
        self.retain(); result = self.observe()
        self.assertEqual(result["receipt_state"], "ABSENT")
        self.assertEqual(result["frame"], safe.UNKNOWN)

    def test_duplicate_keys_rejected_by_native_retention(self):
        raw = json.dumps(receipt())[:-1] + ',"frame":1}'
        self.file.write_text(raw); self.retain()
        self.assertEqual(self.observe()["receipt_state"], "ABSENT")

    def test_nonfinite_fields_are_not_observations(self):
        for key in ("frame", "frame_count", "target_index"):
            value = receipt(); value[key] = float("nan")
            with self.subTest(key=key), self.assertRaises(ValueError): self.native.validate(value, MANIFEST)

    def test_boolean_integer_coercions_rejected(self):
        for key in ("frame", "frame_count", "target_index"):
            value = receipt(); value[key] = True
            with self.subTest(key=key), self.assertRaises(ValueError): self.native.validate(value, MANIFEST)

    def test_bounds_and_target_mode_pairing_rejected(self):
        for field, bad in (("frame", 2), ("frame_count", 2401), ("target_index", 0), ("target_index", -2)):
            value = receipt(); value[field] = bad
            with self.subTest(field=field, bad=bad), self.assertRaises(ValueError): self.native.validate(value, MANIFEST)

    def test_foreign_manifest_rejected(self):
        value = receipt(); value["manifest_sha256"] = "b" * 64
        with self.assertRaises(ValueError): self.native.validate(value, MANIFEST)

    def test_unknown_fields_and_private_content_never_export(self):
        for field in ("stderr", "stdout", "command", "path", "pid", "mapping", "source", "failure"):
            value = receipt(); value[field] = "FAKE_PRIVATE_TOKEN_BOOK_TEXT"
            with self.subTest(field=field), self.assertRaises(ValueError): self.native.validate(value, MANIFEST)
        value = receipt(); value["guard_code"] = "FAKE_PRIVATE_TOKEN_BOOK_TEXT"
        self.put(value); self.retain()
        self.assertNotIn("FAKE_PRIVATE", json.dumps(self.observe()))

    def test_unknown_schema_phase_and_guard_rejected(self):
        for field in ("schema", "phase", "guard_code", "shot_kind"):
            value = receipt(); value[field] = "UNKNOWN_PRIVATE"
            with self.subTest(field=field), self.assertRaises(ValueError): self.native.validate(value, MANIFEST)

    def test_guard_cannot_claim_a_different_observed_phase(self):
        value = receipt(); value["phase"] = "BUNDLE"
        with self.assertRaises(ValueError): self.native.validate(value, MANIFEST)

    def test_accepted_cannot_be_promoted(self):
        value = receipt(); value["accepted"] = True
        with self.assertRaises(ValueError): self.native.validate(value, MANIFEST)

    def test_oversize_native_file_is_not_retained(self):
        self.file.write_bytes(b" " * 1025); self.retain()
        self.assertEqual(self.observe()["receipt_state"], "ABSENT")

    def test_oversize_external_file_explicit_too_large(self):
        (self.out / self.file.name).write_bytes(b" " * 1025)
        self.assertEqual(self.observe()["receipt_state"], "TOO_LARGE")

    def test_partial_and_malformed_external_file_invalid(self):
        (self.out / self.file.name).write_text('{"phase":')
        self.assertEqual(self.observe()["receipt_state"], "INVALID")

    def test_source_link_is_not_retained(self):
        source = self.capture / "private.json"; source.write_text(json.dumps(receipt()))
        self.file.symlink_to(source); self.retain()
        self.assertEqual(self.observe()["receipt_state"], "ABSENT")

    def test_existing_destination_is_not_overwritten(self):
        sentinel = self.out / self.file.name; sentinel.write_text("sentinel")
        self.put(receipt()); self.retain()
        self.assertEqual(sentinel.read_text(), "sentinel")

    def test_retention_failure_does_not_raise_or_delete(self):
        self.put(receipt()); self.native.retain(self.capture, self.root / "missing", MANIFEST)
        self.assertTrue(self.file.exists())

    def test_no_broad_exception_or_process_serialization(self):
        tree = ast.parse((ROOT / "bie/compiler/real_paint.py").read_text())
        node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "_retain_capture_failure_observation")
        for child in ast.walk(node):
            if isinstance(child, ast.Name): self.assertNotIn(child.id, {"repr", "str", "vars", "asdict"})

    def test_closed_reader_error_cannot_export_payload(self):
        value = safe.empty_capture(); value["receipt_state"] = "INVALID"; value["frame"] = "FAKE_PRIVATE"
        self.assertFalse(safe.is_safe_capture_observation(value))

    def test_native_and_external_schema_enum_sets_agree(self):
        for phase in safe.CAPTURE_PHASES:
            value = receipt(); value.update(phase=phase, guard_code="NONE_RECORDED")
            self.assertIs(self.native.validate(value, MANIFEST), value)


FAKE = r'''
const fs=require('node:fs');const req=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
exports.openBrowser=async()=>{
 if(req.test_case==='browser')throw new Error('FAKE_PRIVATE_BROWSER_EXCEPTION');
 return {close:async()=>{fs.appendFileSync(req.output+'/closed.txt','closed');
  if(req.test_case==='close')throw new Error('FAKE_PRIVATE_CLOSE_EXCEPTION');}};
};
exports.selectComposition=async()=>({width:req.width,height:req.height,fps:req.fps,durationInFrames:req.frame_count});
exports.renderStill=async o=>{
 const mode=o.inputProps.__bieRasterMode;
 fs.appendFileSync(req.output+'/calls.jsonl',JSON.stringify({frame:o.frame,mode})+'\n');
 if(req.test_case==='still')throw new Error('FAKE_PRIVATE_STILL_EXCEPTION');
 fs.writeFileSync(o.output,'EXPLICIT_DOUBLE_NOT_PNG');
 const inventory=[{target_id:'synthetic-target',visible:true,box:[0,0,20,20]}];
 if(req.test_case==='drift'&&mode.kind==='muted')inventory[0].box[0]=1;
 const m={nonce:req.nonce,frame:o.frame,records:[],paint_records:[],raster:{mode,inventory,fonts_ready:req.test_case!=='fonts',image_errors:[]}};
 if(req.test_case==='missing')return;
 o.onBrowserLog({type:'log',text:'BIE_PAINT_V1:'+JSON.stringify(m)});
 if(req.test_case==='duplicate'){m.records=[{private_label:'FAKE_PRIVATE_CONTENT'}];o.onBrowserLog({type:'log',text:'BIE_PAINT_V1:'+JSON.stringify(m)});}
};
exports.renderMedia=async o=>{if(req.test_case==='media')throw new Error('FAKE_PRIVATE_MEDIA_EXCEPTION');fs.writeFileSync(o.outputLocation,'EXPLICIT_DOUBLE_NOT_VIDEO');};
'''


class CaptureControllerPlumbing(unittest.TestCase):
    def run_case(self, case, controller=CONTROLLER, diagnostic_blocked=False):
        temporary = tempfile.TemporaryDirectory(); self.addCleanup(temporary.cleanup)
        root = Path(temporary.name); out = root / "out"; out.mkdir()
        (root / "package.json").write_text('{}')
        for name in ("remotion", "@remotion/renderer", "@remotion/bundler"):
            folder = root / "node_modules" / name; folder.mkdir(parents=True)
            (folder / "package.json").write_text(json.dumps({"name": name, "version": "4.0.506", "main": "index.js"}))
            (folder / "index.js").write_text(FAKE if name.endswith("renderer") else 'exports.bundle=async()=>"EXPLICIT_DOUBLE_BUNDLE";')
        request = {"workspace": str(root), "output": str(out), "browser": "explicit-double", "remotion_version": "4.0.506",
            "test_case": case, "nonce": "SYNTHETIC_NONCE", "manifest_sha256": MANIFEST, "scene_sha256": "b" * 64,
            "composition_id": "Test", "width": 640, "height": 360, "fps": 4, "frame_count": 2,
            "rasterTargets": [{"target_id": "synthetic-target"}], "equationFonts": {}}
        path = root / "request.json"; path.write_text(json.dumps(request))
        if diagnostic_blocked: (out / "CAPTURE_PROCESS_DIAGNOSTIC.json").mkdir()
        result = subprocess.run(["node", str(controller), str(path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=15)
        return result.returncode, out

    def diagnostic(self, case):
        code, out = self.run_case(case)
        self.assertEqual(code, 2)
        value = json.loads((out / "CAPTURE_PROCESS_DIAGNOSTIC.json").read_text())
        self.assertNotIn("FAKE_PRIVATE", json.dumps(value))
        pure_native_reader().validate(value, MANIFEST)
        return value, out

    def test_success_legacy_result_bytes_and_calls_unchanged(self):
        old_code, old = self.run_case("ok", BEFORE); code, out = self.run_case("ok")
        self.assertEqual((old_code, code), (0, 0))
        for name in ("RESULT.json", "calls.jsonl", "closed.txt"):
            self.assertEqual((old / name).read_bytes(), (out / name).read_bytes())
        self.assertFalse((out / "CAPTURE_PROCESS_DIAGNOSTIC.json").exists())

    def test_original_missing_measurement_rejection_and_cleanup_preserved(self):
        old_code, old = self.run_case("missing", BEFORE); value, out = self.diagnostic("missing")
        self.assertEqual(old_code, 2)
        self.assertEqual(value["guard_code"], "CAPTURE_DOM_MEASUREMENT_MISSING")
        self.assertEqual((out / "closed.txt").read_bytes(), (old / "closed.txt").read_bytes())

    def test_nondeterministic_observer_static_guard_observed(self):
        value, _ = self.diagnostic("duplicate")
        self.assertEqual((value["phase"], value["guard_code"]), ("MEASUREMENT_CHECK", "CAPTURE_DOM_NONDETERMINISM"))

    def test_mode_drift_guard_does_not_become_success(self):
        value, _ = self.diagnostic("drift")
        self.assertEqual((value["phase"], value["guard_code"], value["shot_kind"]), ("MODE_INVENTORY", "CAPTURE_DOM_MODE_DRIFT", "MUTED"))

    def test_font_readiness_guard_is_not_a_renderer_cause_guess(self):
        value, _ = self.diagnostic("fonts")
        self.assertEqual(value["guard_code"], "CAPTURE_ASSET_READINESS")

    def test_foreign_library_exception_exposes_only_actual_phase(self):
        for case, phase in (("browser", "OPEN_BROWSER"), ("still", "RENDER_STILL"), ("media", "RENDER_MEDIA")):
            with self.subTest(case=case):
                value, _ = self.diagnostic(case)
                self.assertEqual((value["phase"], value["guard_code"]), (phase, "NONE_RECORDED"))

    def test_browser_cleanup_exception_retains_actual_phase(self):
        value, _ = self.diagnostic("close")
        self.assertEqual(value["phase"], "BROWSER_CLOSE")

    def test_failure_diagnostic_writer_cannot_mask_original_exit(self):
        code, out = self.run_case("missing", diagnostic_blocked=True)
        self.assertEqual(code, 2)
        self.assertEqual((out / "closed.txt").read_text(), "closed")


class CaptureSourceAmendment(unittest.TestCase):
    """Exact replacement/preimage chain checks, not independent approval."""
    @classmethod
    def setUpClass(cls):
        from scripts import compiler_capture_observation_amendment as amendment
        cls.amendment = amendment
        cls.temporary = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temporary.cleanup)
        cls.fixture = Path(cls.temporary.name)
        doc = amendment.validate(ROOT)
        cls.document = doc
        from scripts.compiler_cache_source_amendment import MANIFEST
        selected = {amendment.DOCUMENT, amendment.M1_DOCUMENT, "manifests/" + MANIFEST}
        selected.update(r["path"] for r in doc["replacements"])
        selected.update(r["preimage"] for r in doc["replacements"])
        # The sealed old assertions now exercise the complete exact follow-on
        # chain, rather than substituting old sources for current active bytes.
        from scripts import compiler_media_observation_amendment as media_amendment
        media_doc = media_amendment.validate(ROOT)
        selected.add(media_amendment.DOCUMENT)
        selected.update(r["path"] for r in media_doc["replacements"])
        selected.update(r["preimage"] for r in media_doc["replacements"])
        from scripts import compiler_media_thread_amendment as threads
        thread_doc = threads.validate(ROOT)
        selected.add(threads.DOCUMENT)
        selected.update(r["path"] for r in thread_doc["replacements"] + thread_doc["additions"])
        selected.update(r["preimage"] for r in thread_doc["replacements"])
        for relative in selected:
            target = cls.fixture / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, target)

    def alter(self, relative, change):
        """Restore the exact test fixture only; never changes repository source."""
        path = self.fixture / relative
        original = path.read_bytes()
        self.addCleanup(path.write_bytes, original)
        path.write_bytes(change(original))

    def test_exact_active_and_preimage_chain_validates(self):
        self.assertEqual(self.amendment.validate(self.fixture), self.document)
        for row in self.document["replacements"]:
            if row["path"] in self.amendment.NATIVE_TARGETS:
                self.assertEqual(self.amendment.authenticated_previous_bytes(self.fixture,
                    row["path"], row["original_sha256"]), (self.fixture / row["preimage"]).read_bytes())

    def test_each_active_path_tamper_rejected(self):
        for row in self.document["replacements"]:
            with self.subTest(path=row["path"]):
                path = self.fixture / row["path"]; original = path.read_bytes()
                try:
                    path.write_bytes(original + b"# unauthorized\n")
                    with self.assertRaises(ValueError): self.amendment.validate(self.fixture)
                finally: path.write_bytes(original)

    def test_each_preimage_tamper_rejected(self):
        for row in self.document["replacements"]:
            with self.subTest(path=row["preimage"]):
                path = self.fixture / row["preimage"]; original = path.read_bytes()
                try:
                    path.write_bytes(original + b"tamper")
                    with self.assertRaises(ValueError): self.amendment.validate(self.fixture)
                finally: path.write_bytes(original)

    def test_manifest_tamper_cannot_self_bless_current_hash(self):
        self.alter(self.amendment.DOCUMENT, lambda value: value.replace(b'"PENDING_SEPARATE_REVIEW"', b'"APPROVED"'))
        with self.assertRaises(ValueError): self.amendment.validate(self.fixture)

    def test_duplicate_or_extra_replacement_is_not_authorized(self):
        for variant in ("duplicate", "extra"):
            path = self.fixture / self.amendment.DOCUMENT; original = path.read_bytes()
            try:
                doc = json.loads(original)
                row = deepcopy(doc["replacements"][0])
                if variant == "extra": row["path"] = "bie/compiler/unlisted.py"
                doc["replacements"].append(row)
                path.write_bytes(canonical_json(doc))
                with self.assertRaises(ValueError): self.amendment.validate(self.fixture)
            finally: path.write_bytes(original)

    def test_old_sealed_amendment_and_manifest_cannot_be_changed(self):
        from scripts.compiler_cache_source_amendment import MANIFEST
        for relative in (self.amendment.M1_DOCUMENT, "manifests/" + MANIFEST):
            with self.subTest(path=relative):
                path = self.fixture / relative; original = path.read_bytes()
                try:
                    path.write_bytes(original + b" ")
                    with self.assertRaises(ValueError): self.amendment.validate(self.fixture)
                finally: path.write_bytes(original)

    def test_unlisted_target_and_wrong_parent_identity_rejected(self):
        with self.assertRaises(ValueError):
            self.amendment.authenticated_previous_bytes(self.fixture, "bie/compiler/unlisted.py", "a" * 64)
        with self.assertRaises(ValueError):
            self.amendment.authenticated_previous_bytes(self.fixture, next(iter(self.amendment.NATIVE_TARGETS)), "a" * 64)

    def test_native_worker_calls_and_limits_are_identical_to_preimage(self):
        def calls(path):
            tree = ast.parse(path.read_text())
            return [ast.dump(n, include_attributes=False) for n in ast.walk(tree)
                    if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                    and n.func.id in {"run_chromium_isolated", "WorkerPolicy"}]
        directory = ROOT / "docs/productization/task036-capture-observation-amendment"
        self.assertEqual(calls(ROOT / "bie/compiler/real_paint.py"), calls(directory / "real_paint.py.before"))
        self.assertTrue(self.document["native_calls_and_limits_unchanged"])


if __name__ == "__main__": unittest.main()
