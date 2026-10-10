"""Diagnostic contract controls, not native Linux media/render proof."""
import ast
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from bie.compiler.artifact_hashing import canonical_json
from tests.compiler import m1_media_diagnostics as media
from tests.compiler.test_m1_capture_diagnostics import pure_native_reader

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = "a" * 64
CONTROLLER = ROOT / "bie/compiler/qa_support/remotion_raster_capture.cjs"


def native_media_reader():
    tree = ast.parse((ROOT / "bie/compiler/real_paint.py").read_text())
    selected = [n for n in tree.body if isinstance(n, ast.FunctionDef) and
        n.name in {"validate_media_failure_observation", "_retain_media_failure_observation"}]
    assert len(selected) == 2
    namespace = {"Path": Path, "json": json, "canonical_json": canonical_json}
    exec(compile(ast.Module(selected, type_ignores=[]), "canonical_pure_media_reader", "exec"), namespace)
    return SimpleNamespace(validate=namespace["validate_media_failure_observation"],
        retain=namespace["_retain_media_failure_observation"])


def raw_receipt():
    return {"schema": "bie.capture-media-process-failure/1", "phase": "RENDER_MEDIA",
        "manifest_sha256": MANIFEST, "frame_count": 48, "state": "VALID", "spawn_events": 1,
        "events": [{"event": "EXIT", "exit_code": 1, "signal": "UNKNOWN", "error_code": "UNKNOWN"}],
        "accepted": False}


class MediaSafeReader(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(); self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.capture = self.root / "capture"; self.capture.mkdir()
        self.out = self.root / "paint-reduced"; self.out.mkdir()
        self.file = self.capture / "MEDIA_PROCESS_DIAGNOSTIC.json"
        self.native = native_media_reader()

    def observe(self):
        return media.capture_media_observation(self.root, preference="reduced", manifest_sha256=MANIFEST, frame_count=48)

    def put(self, value): self.file.write_text(json.dumps(value))
    def retain(self): self.native.retain(self.capture, self.out, MANIFEST)

    def test_valid_failure_is_not_render_acceptance(self):
        self.put(raw_receipt()); self.retain(); value = self.observe()
        self.assertTrue(media.is_safe_media(value)); self.assertEqual(value["events"][0]["exit_code"], 1)
        self.assertFalse(value["render_passed"]); self.assertFalse(value["accepted"])

    def test_unavailable_remains_unknown_not_zero(self):
        value = raw_receipt(); value.update(state="UNAVAILABLE", events=[], spawn_events="UNKNOWN")
        self.put(value); self.retain()
        self.assertEqual(self.observe(), media.empty_media("UNAVAILABLE"))

    def test_absent_no_zero_exit_or_success_inference(self):
        self.retain(); self.assertEqual(self.observe(), media.empty_media("ABSENT"))

    def test_raw_reader_budget_unchanged(self):
        (self.out / self.file.name).write_bytes(b" " * 1025)
        self.assertEqual(self.observe(), media.empty_media("TOO_LARGE"))

    def test_native_oversize_not_retained(self):
        self.file.write_bytes(b" " * 1025); self.retain()
        self.assertEqual(self.observe()["receipt_state"], "ABSENT")

    def test_malformed_and_duplicate_json_never_retained(self):
        for raw in ('{"schema":', json.dumps(raw_receipt())[:-1] + ',"accepted":false}'):
            self.file.write_text(raw); self.retain(); self.assertFalse((self.out / self.file.name).exists())

    def test_nonfinite_boolean_integer_and_bounds_rejected(self):
        for field, value in (("spawn_events", True), ("spawn_events", -1), ("spawn_events", 129), ("frame_count", False), ("frame_count", float("nan"))):
            receipt = raw_receipt(); receipt[field] = value
            with self.subTest(field=field, value=value), self.assertRaises(ValueError): self.native.validate(receipt, MANIFEST)

    def test_foreign_manifest_and_frame_count_rejected(self):
        value = raw_receipt(); value["manifest_sha256"] = "b" * 64
        self.put(value); self.retain(); self.assertEqual(self.observe()["receipt_state"], "ABSENT")
        value = raw_receipt(); value["frame_count"] = 47
        (self.out / self.file.name).write_text(json.dumps(value)); self.assertEqual(self.observe()["receipt_state"], "INVALID")

    def test_unknown_nested_fields_never_export(self):
        for field in ("stderr", "stdout", "command", "path", "pid", "grants", "source", "error"):
            value = raw_receipt(); value["events"][0][field] = "FAKE_PRIVATE_BOOK_TOKEN"
            self.put(value); self.retain()
            self.assertEqual(self.observe()["receipt_state"], "ABSENT")
            self.assertNotIn("FAKE_PRIVATE", json.dumps(self.observe()))

    def test_unknown_enum_and_event_pair_rejected(self):
        for field, bad in (("signal", "PRIVATE"), ("error_code", "PRIVATE"), ("exit_code", True), ("exit_code", 256), ("event", "CLOSE")):
            value = raw_receipt(); value["events"][0][field] = bad
            with self.subTest(field=field), self.assertRaises(ValueError): self.native.validate(value, MANIFEST)
        value = raw_receipt(); value["events"][0]["event"] = "ERROR"
        with self.assertRaises(ValueError): self.native.validate(value, MANIFEST)

    def test_valid_error_code_and_signal_do_not_infer_cause(self):
        for row in ({"event": "ERROR", "error_code": "EAGAIN", "signal": "UNKNOWN", "exit_code": "UNKNOWN"},
                    {"event": "EXIT", "error_code": "UNKNOWN", "signal": "SIGKILL", "exit_code": "UNKNOWN"}):
            value = raw_receipt(); value["events"] = [row]
            self.assertIs(self.native.validate(value, MANIFEST), value)

    def test_event_limit_closed_and_acceptance_rejected(self):
        value = raw_receipt(); value["events"] *= 5
        with self.assertRaises(ValueError): self.native.validate(value, MANIFEST)
        value = raw_receipt(); value["accepted"] = True
        with self.assertRaises(ValueError): self.native.validate(value, MANIFEST)

    def test_retention_preserves_existing_destination_and_cleanup(self):
        destination = self.out / self.file.name; destination.write_text("sentinel")
        self.put(raw_receipt()); self.retain()
        self.assertEqual(destination.read_text(), "sentinel"); self.assertTrue(self.file.exists())
        self.native.retain(self.capture, self.root / "missing", MANIFEST)

    def test_historical_capture_reader_nodes_remain_exact(self):
        self.assertIsNotNone(pure_native_reader())


class MediaEventPlumbing(unittest.TestCase):
    def run_node(self, body, setup=""):
        # Extract the ACTUAL implementation, with explicit event doubles only.
        source = CONTROLLER.read_text()
        start = source.index("async function observeMedia(call){")
        end = source.index("const observation=", start)
        observer = source[start:end]
        script = r'''
const {EventEmitter}=require('node:events');const {types}=require('node:util');
class ChildProcess extends EventEmitter{};
const nativeRequire=require;
function safeRequire(name){return name==='node:child_process'?{ChildProcess}:nativeRequire(name);}
const observation={manifest_sha256:'a'.repeat(64),frame_count:48};
let mediaFailure=null;
''' + setup + "\n" + observer.replace("require(", "safeRequire(") + "\n" + r'''
(async()=>{const proof={};
''' + body + r'''
console.log(JSON.stringify(proof));})().catch(()=>{process.exitCode=1;});
'''
        result = subprocess.run(["node", "-e", script], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=15, check=True)
        value = json.loads(result.stdout); self.assertNotIn("FAKE_PRIVATE", json.dumps(value)); return value

    def test_once_unchanged_return_and_binding_descriptor_restored(self):
        value = self.run_node("""const expected={};let calls=0;const prior=Object.getOwnPropertyDescriptor(ChildProcess.prototype,'emit');
const got=await observeMedia(async()=>{calls++;return expected;});
proof.once=calls===1;proof.same=got===expected;proof.binding=Object.getOwnPropertyDescriptor(ChildProcess.prototype,'emit')===prior;proof.absent=mediaFailure===null;""")
        self.assertEqual(value, {"once": True, "same": True, "binding": True, "absent": True})

    def test_original_exception_identity_cleanup_and_finite_events(self):
        value = self.run_node("""const error=new Error('FAKE_PRIVATE_BOOK_TOKEN');let caught,clean=false;
try{await observeMedia(async()=>{try{const child=new ChildProcess();child.emit('spawn');child.emit('exit',1,null);throw error;}finally{clean=true;}});}catch(e){caught=e;}
proof.same=caught===error;proof.clean=clean;proof.record=mediaFailure;proof.restored=!Object.hasOwn(ChildProcess.prototype,'emit');""")
        self.assertTrue(value["same"] and value["clean"] and value["restored"])
        self.assertEqual(value["record"]["events"][0]["exit_code"], 1)

    def test_private_error_messages_and_getters_never_read(self):
        value = self.run_node("""let reads=0;const error=new Error();Object.defineProperty(error,'message',{get:()=>{reads++;throw new Error();}});
Object.defineProperty(error,'code',{get:()=>{reads++;return 'EAGAIN';}});
try{await observeMedia(async()=>{const child=new ChildProcess();child.on('error',()=>{});child.emit('error',error);throw error;});}catch(_){}
proof.reads=reads;proof.record=mediaFailure;""")
        self.assertEqual(value["reads"], 0); self.assertEqual(value["record"]["events"][0]["error_code"], "UNKNOWN")

    def test_error_scalar_and_signal_are_exact_not_outer_exit_inference(self):
        value = self.run_node("""try{await observeMedia(async()=>{const child=new ChildProcess();child.on('error',()=>{});
const error=new Error('FAKE_PRIVATE');error.code='EAGAIN';child.emit('error',error);child.emit('exit',null,'SIGTERM');throw error;});}catch(_){}
proof.record=mediaFailure;""")
        self.assertEqual(value["record"]["events"][0]["error_code"], "EAGAIN")
        self.assertEqual(value["record"]["events"][1]["signal"], "SIGTERM")
        self.assertEqual(value["record"]["events"][1]["exit_code"], "UNKNOWN")

    def test_overflow_is_unavailable_not_partial_proof(self):
        value = self.run_node("""try{await observeMedia(async()=>{const child=new ChildProcess();for(let i=0;i<5;i++)child.emit('exit',1,null);throw new Error();});}catch(_){}
proof.record=mediaFailure;""")
        self.assertEqual(value["record"]["state"], "UNAVAILABLE"); self.assertEqual(value["record"]["events"], [])

    def test_original_emit_return_and_throw_identity_preserved(self):
        value = self.run_node("""const error=new Error();let caught,returned;const child=new ChildProcess();child.on('custom',()=>{throw error;});
try{await observeMedia(async()=>{returned=child.emit('no-listeners','FAKE_PRIVATE');child.emit('custom');});}catch(e){caught=e;}
proof.same=caught===error;proof.result=returned===false;""")
        self.assertEqual(value, {"same": True, "result": True})

    def test_fake_error_proxy_getters_cannot_export_or_mask(self):
        value = self.run_node("""let reads=0;const error=new Proxy(new Error('FAKE_PRIVATE'),{get:()=>{reads++;throw new Error();},getOwnPropertyDescriptor:()=>{reads++;throw new Error();}});
try{await observeMedia(async()=>{const child=new ChildProcess();child.on('error',()=>{});child.emit('error',error);throw error;});}catch(e){proof.same=e===error;}
proof.reads=reads;proof.record=mediaFailure;""")
        self.assertEqual(value["reads"], 0); self.assertTrue(value["same"])
        self.assertEqual(value["record"]["events"][0]["error_code"], "UNKNOWN")

    def test_nonwritable_binding_falls_back_once_without_masking(self):
        value = self.run_node("let calls=0;const result={};proof.same=(await observeMedia(async()=>{calls++;return result;}))===result;proof.once=calls===1;",
            "Object.defineProperty(ChildProcess.prototype,'emit',{value:EventEmitter.prototype.emit,writable:false,configurable:false});")
        self.assertEqual(value, {"same": True, "once": True})

    def test_existing_own_descriptor_restored(self):
        value = self.run_node("const before=Object.getOwnPropertyDescriptor(ChildProcess.prototype,'emit');await observeMedia(async()=>{});const after=Object.getOwnPropertyDescriptor(ChildProcess.prototype,'emit');proof.same=before.value===after.value&&before.enumerable===after.enumerable&&before.writable===after.writable&&before.configurable===after.configurable;",
            "Object.defineProperty(ChildProcess.prototype,'emit',{value:EventEmitter.prototype.emit,writable:true,configurable:true,enumerable:true});")
        self.assertEqual(value, {"same": True})

    def test_setup_getter_failure_falls_back_exactly_once_and_restores(self):
        value = self.run_node("const before=Object.getOwnPropertyDescriptor(ChildProcess.prototype,'emit');let calls=0;const expected={};proof.same=(await observeMedia(async()=>{calls++;return expected;}))===expected;proof.once=calls===1;proof.binding=Object.getOwnPropertyDescriptor(ChildProcess.prototype,'emit').get===before.get;proof.absent=mediaFailure===null;",
            "Object.defineProperty(ChildProcess.prototype,'emit',{get(){throw new Error('FAKE_PRIVATE');},configurable:true});")
        self.assertEqual(value, {"same": True, "once": True, "binding": True, "absent": True})

    def test_setup_error_cannot_replace_original_media_exception(self):
        value = self.run_node("let calls=0;const error=new Error('FAKE_PRIVATE');try{await observeMedia(async()=>{calls++;throw error;});}catch(e){proof.same=e===error;}proof.once=calls===1;proof.absent=mediaFailure===null;",
            "Object.defineProperty(ChildProcess.prototype,'emit',{get(){throw new Error('setup');},configurable:true});")
        self.assertEqual(value, {"same": True, "once": True, "absent": True})


class OwnedPidControls(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(); self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name).resolve()
        self.group = self.base / "bie-chromium-owned-synthetic"; self.group.mkdir()
        (self.group / "pids.max").write_bytes(b"128\n")
        (self.group / "pids.events").write_bytes(b"max 3\n")
        (self.group / "pids.peak").write_bytes(b"127\n")
        self.inode = self.group.stat().st_ino

    def read(self): return media.owned_pid_controls(self.group, self.inode, self.base)

    def test_fixed_readonly_counters_not_a_memory_cause(self):
        self.assertEqual(self.read(), (3, 127))
        self.assertEqual((self.group / "pids.max").read_bytes(), b"128\n")

    def test_optional_peak_absent_remains_unknown(self):
        (self.group / "pids.peak").unlink(); self.assertEqual(self.read(), (3, "UNKNOWN"))

    def test_missing_counter_not_zero(self):
        (self.group / "pids.events").unlink()
        with self.assertRaises(FileNotFoundError): self.read()

    def test_duplicate_unknown_negative_overflow_and_private_control_rejected(self):
        for raw in (b"max 1\nmax 2\n", b"private 2\n", b"max -1\n", b"max 9999999999999999999\n", b"FAKE_PRIVATE_TOKEN", b"x" * 257):
            (self.group / "pids.events").write_bytes(raw)
            with self.subTest(raw_kind=len(raw)), self.assertRaises(ValueError): self.read()

    def test_foreign_root_inode_and_limit_rejected(self):
        with self.assertRaises(ValueError): media.owned_pid_controls(self.group, self.inode + 1, self.base)
        with self.assertRaises(ValueError): media.owned_pid_controls(self.group, self.inode, self.base / "foreign")
        (self.group / "pids.max").write_bytes(b"129\n")
        with self.assertRaises(ValueError): self.read()

    def test_delegate_once_identical_return_and_scalar_retention(self):
        group = SimpleNamespace(path=self.group, inode=self.inode)
        private = {"pids_max": 128, "stderr": "FAKE_PRIVATE" * 300000, "command": object()}
        calls = []; observer = media.PidObserver()
        got = observer.delegate(lambda supplied: calls.append(supplied) or private, group, base=self.base, expected_type=SimpleNamespace)
        self.assertIs(got, private); self.assertEqual(calls, [group])
        self.assertTrue(media.is_safe_pids(observer.snapshot()))
        self.assertEqual(observer.snapshot()["max_events"], 3)
        self.assertNotIn("FAKE_PRIVATE", json.dumps(observer.snapshot()))

    def test_exception_identity_not_masked_by_observer_error(self):
        observer = media.PidObserver(); original = ValueError("FAKE_PRIVATE")
        def fail(_): raise original
        with patch.object(media, "empty_pids", side_effect=RuntimeError("observer")):
            with self.assertRaises(ValueError) as caught: observer.delegate(fail, object(), base=self.base, expected_type=object)
        self.assertIs(caught.exception, original)

    def test_control_failure_cannot_mask_original_return(self):
        observer = media.PidObserver(); expected = {"pids_max": 128}; group = SimpleNamespace(path=self.group, inode=self.inode)
        with patch.object(media, "owned_pid_controls", side_effect=RuntimeError("private")):
            self.assertIs(observer.delegate(lambda _: expected, group, base=self.base, expected_type=SimpleNamespace), expected)
        self.assertEqual(observer.snapshot()["availability"], "UNAVAILABLE")

    def test_multiple_calls_not_misrepresented_as_single_counter_sample(self):
        observer = media.PidObserver(); group = SimpleNamespace(path=self.group, inode=self.inode)
        for _ in range(2): observer.delegate(lambda _: {"pids_max": 128}, group, base=self.base, expected_type=SimpleNamespace)
        self.assertEqual(observer.snapshot()["stage"], "MULTIPLE_CALLS")

    def test_raised_then_returned_invocations_remain_multiple_unknown(self):
        observer = media.PidObserver(); group = SimpleNamespace(path=self.group, inode=self.inode)
        error = ValueError("private")
        def fail(_): raise error
        with self.assertRaises(ValueError) as caught: observer.delegate(fail, group, base=self.base, expected_type=SimpleNamespace)
        self.assertIs(caught.exception, error)
        expected = {"pids_max": 128}
        self.assertIs(observer.delegate(lambda _: expected, group, base=self.base, expected_type=SimpleNamespace), expected)
        self.assertEqual(observer.calls, 2)
        self.assertEqual(observer.snapshot()["stage"], "MULTIPLE_CALLS")
        self.assertEqual(observer.snapshot()["max_events"], "UNKNOWN")

    def test_returned_then_raised_invocations_preserve_exception_and_unknown(self):
        observer = media.PidObserver(); group = SimpleNamespace(path=self.group, inode=self.inode)
        observer.delegate(lambda _: {"pids_max": 128}, group, base=self.base, expected_type=SimpleNamespace)
        error = ValueError("private")
        def fail(_): raise error
        with self.assertRaises(ValueError) as caught: observer.delegate(fail, group, base=self.base, expected_type=SimpleNamespace)
        self.assertIs(caught.exception, error); self.assertEqual(observer.calls, 2)
        self.assertEqual(observer.snapshot()["stage"], "MULTIPLE_CALLS")
        self.assertEqual(observer.snapshot()["max_events"], "UNKNOWN")

    def test_closed_schema_boolean_integer_and_private_field_rejected(self):
        value = media.empty_pids("NONE"); value.update(availability="VALID", pids_max=128, max_events=0, peak_tasks="UNKNOWN")
        self.assertTrue(media.is_safe_pids(value))
        for field, item in (("max_events", True), ("pids_max", 129), ("peak_tasks", -1), ("stdout", "FAKE_PRIVATE")):
            candidate = dict(value); candidate[field] = item
            self.assertFalse(media.is_safe_pids(candidate))

    def test_canonical_binding_restored_on_success_and_original_exception(self):
        from bie.compiler import chromium_resource_worker as worker
        original = worker.OwnedMemoryGroup.receipt
        with media.observe_owned_pids() as observer:
            self.assertIsNot(worker.OwnedMemoryGroup.receipt, original)
        self.assertIs(worker.OwnedMemoryGroup.receipt, original)
        error = ValueError("private")
        with self.assertRaises(ValueError) as caught:
            with media.observe_owned_pids(): raise error
        self.assertIs(caught.exception, error); self.assertIs(worker.OwnedMemoryGroup.receipt, original)

    def test_observer_constructor_failure_cannot_replace_painter_or_binding(self):
        from bie.compiler import chromium_resource_worker as worker
        original = worker.OwnedMemoryGroup.receipt
        error = ValueError("original")
        with patch.object(media, "PidObserver", side_effect=RuntimeError("observer")):
            with self.assertRaises(ValueError) as caught:
                with media.observe_owned_pids() as observer:
                    self.assertIsNone(observer)
                    raise error
        self.assertIs(caught.exception, error); self.assertIs(worker.OwnedMemoryGroup.receipt, original)

    def test_no_whole_object_serialization_or_private_field_reads(self):
        tree = ast.parse((ROOT / "tests/compiler/m1_media_diagnostics.py").read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                self.assertNotIn(node.func.id, {"asdict", "repr", "str", "vars"})
            if isinstance(node, ast.Constant) and type(node.value) is str:
                self.assertNotIn(node.value, {"stdout", "stderr", "command", "driver_stderr", "grants", "mappings"})


class MediaAmendmentChain(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from scripts import compiler_media_observation_amendment as amendment
        from scripts import compiler_capture_observation_amendment as previous
        from scripts.compiler_cache_source_amendment import MANIFEST
        cls.amendment, cls.previous = amendment, previous
        cls.doc = amendment.validate(ROOT)
        cls.old_doc = previous.validate(ROOT)
        cls.temporary = tempfile.TemporaryDirectory(); cls.addClassCleanup(cls.temporary.cleanup)
        cls.root = Path(cls.temporary.name)
        paths = {amendment.DOCUMENT, amendment.PREVIOUS_DOCUMENT, amendment.M1_DOCUMENT,
            "manifests/" + MANIFEST, "scripts/compiler_cache_source_amendment.py"}
        for doc in (cls.doc, cls.old_doc):
            paths.update(row["path"] for row in doc["replacements"])
            paths.update(row["preimage"] for row in doc["replacements"])
        for name in paths:
            target = cls.root / name; target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((ROOT / name).read_bytes())

    def test_fixed_complete_chain_and_exact_parent_blobs(self):
        import hashlib
        self.assertEqual(self.amendment.validate(self.root), self.doc)
        self.assertEqual(self.previous.validate(self.root), self.old_doc)
        for row in self.doc["replacements"]:
            source = subprocess.run(["git", "show", "ea46f209babedfb6684114a79b4d39bda2e73913:" + row["path"]],
                cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=True).stdout
            self.assertEqual(source, (self.root / row["preimage"]).read_bytes())
            self.assertEqual(hashlib.sha256(source).hexdigest(), row["original_sha256"])

    def test_all_active_and_preimage_tampers_fail_closed(self):
        for row in self.doc["replacements"]:
            for field in ("path", "preimage"):
                path = self.root / row[field]; original = path.read_bytes()
                try:
                    path.write_bytes(original + b"UNAUTHORIZED\n")
                    with self.assertRaises(ValueError): self.amendment.validate(self.root)
                    with self.assertRaises(ValueError): self.previous.validate(self.root)
                finally: path.write_bytes(original)

    def test_manifest_duplicate_extra_scope_cannot_self_bless(self):
        path = self.root / self.amendment.DOCUMENT; original = path.read_bytes()
        try:
            for kind in ("duplicate", "extra", "changedhash"):
                doc = deepcopy(self.doc)
                if kind == "changedhash": doc["replacements"][0]["active_sha256"] = "f" * 64
                else:
                    row = deepcopy(doc["replacements"][0])
                    if kind == "extra": row["path"] = "bie/compiler/unlisted.py"
                    doc["replacements"].append(row)
                path.write_bytes(canonical_json(doc))
                with self.assertRaises(ValueError): self.amendment.validate(self.root)
        finally: path.write_bytes(original)

    def test_old_amendments_and_prior_audit_remain_pinned(self):
        for relative in (self.amendment.PREVIOUS_DOCUMENT, self.amendment.M1_DOCUMENT,
                         "scripts/compiler_cache_source_amendment.py"):
            path = self.root / relative; original = path.read_bytes()
            try:
                path.write_bytes(original + b" ")
                with self.assertRaises(ValueError): self.amendment.validate(self.root)
            finally: path.write_bytes(original)

    def test_unlisted_and_foreign_previous_identity_rejected(self):
        with self.assertRaises(ValueError): self.amendment.authenticated_previous_bytes(self.root, "bie/compiler/unlisted.py", "a" * 64)
        with self.assertRaises(ValueError): self.amendment.authenticated_previous_bytes(self.root, next(iter(self.amendment.NATIVE_TARGETS)), "a" * 64)

    def test_exact_native_rollback_cannot_evade_latest_amendment(self):
        originals = {}
        try:
            for row in self.doc["replacements"]:
                if row["path"] in self.amendment.NATIVE_TARGETS:
                    path = self.root / row["path"]; originals[path] = path.read_bytes()
                    path.write_bytes((self.root / row["preimage"]).read_bytes())
            with self.assertRaises(ValueError): self.previous.validate(self.root)
        finally:
            for path, raw in originals.items(): path.write_bytes(raw)

    def test_historical_resolver_rejects_missing_or_tampered_latest_document(self):
        path = self.root / self.amendment.DOCUMENT; original = path.read_bytes()
        try:
            path.write_bytes(original + b" ")
            with self.assertRaises(ValueError): self.previous.validate(self.root)
            path.unlink()
            with self.assertRaises((ValueError, FileNotFoundError)): self.previous.validate(self.root)
        finally: path.write_bytes(original)

    def test_original_render_settings_and_limits_are_not_changed(self):
        before = (ROOT / self.doc["replacements"][0]["preimage"]).read_text()
        current = CONTROLLER.read_text()
        start = "renderMedia({composition,serveUrl,outputLocation,codec:'h264',pixelFormat:'yuv420p',concurrency:1,puppeteerInstance:browser,\n    inputProps:{__bieRasterMode:{kind:'full'}}})"
        self.assertIn(start, before); self.assertIn(start, current)
        before_paint = ast.parse((ROOT / self.doc["replacements"][1]["preimage"]).read_text())
        current_paint = ast.parse((ROOT / "bie/compiler/real_paint.py").read_text())
        for name in ("run_chromium_isolated", "isolated_typecheck", "inspect_owner_fit", "inspect_paint_quality", "inspect_counterfactual_capture", "require_same_toolchain"):
            def calls(tree):
                return [ast.dump(n, include_attributes=False) for n in ast.walk(tree) if isinstance(n, ast.Call)
                    and isinstance(n.func, ast.Name) and n.func.id == name]
            self.assertEqual(calls(before_paint), calls(current_paint), name)


class MediaWrapperRetention(unittest.TestCase):
    def test_failure_record_retained_before_temporary_cleanup_without_promotion(self):
        from tests.compiler.test_m1_safe_paint_diagnostics import TypedWrapperRetention
        from tests.compiler.run_motion_m1 import safe_error
        original = ValueError("ACTUAL_PAINT_EXECUTION_BLOCKED:FAKE_PRIVATE")
        temporary = tempfile.TemporaryDirectory(); root = Path(temporary.name).resolve()
        try:
            def painter(*args, **kw):
                output = root / "paint-standard"; output.mkdir()
                (output / "MEDIA_PROCESS_DIAGNOSTIC.json").write_text(json.dumps(raw_receipt()))
                raise original
            helper = TypedWrapperRetention()
            ns = helper.namespace(root, painter)
            ns["receipt"] = SimpleNamespace(manifest_sha256=MANIFEST)
            with self.assertRaises(ValueError) as caught: exec(helper.block(), ns)
            self.assertIs(caught.exception, original)
            self.assertEqual(ns["phase"]["media_process_observation"]["events"][0]["exit_code"], 1)
            self.assertEqual(ns["phase"]["owned_pid_observation"]["stage"], "NOT_CALLED")
            self.assertFalse(ns["phase"]["render_passed"])
            self.assertEqual(safe_error(original)["safe_code"], "ACTUAL_PAINT_EXECUTION_BLOCKED")
            safe_record = dict(ns["phase"]["media_process_observation"])
        finally: temporary.cleanup()
        self.assertFalse(root.exists()); self.assertTrue(media.is_safe_media(safe_record))

    def test_observer_exception_and_private_counterfeit_cannot_mask_painter(self):
        from tests.compiler.test_m1_safe_paint_diagnostics import TypedWrapperRetention
        original = ValueError("FAKE_PRIVATE")
        def painter(*args, **kw): raise original
        with tempfile.TemporaryDirectory() as td:
            helper = TypedWrapperRetention(); ns = helper.namespace(Path(td).resolve(), painter)
            ns["receipt"] = SimpleNamespace(manifest_sha256=MANIFEST)
            for replacement in (lambda *a, **kw: {"stdout": "FAKE_PRIVATE"},
                                lambda *a, **kw: (_ for _ in ()).throw(RuntimeError("FAKE_PRIVATE"))):
                with patch.object(media, "capture_media_observation", replacement):
                    with self.assertRaises(ValueError) as caught: exec(helper.block(), ns)
                self.assertIs(caught.exception, original)
                self.assertNotIn("media_process_observation", ns["phase"])

    def test_success_does_not_read_failure_files_or_export_pid_snapshot(self):
        from tests.compiler.test_m1_safe_paint_diagnostics import TypedWrapperRetention
        sentinel = object()
        with tempfile.TemporaryDirectory() as td:
            helper = TypedWrapperRetention(); ns = helper.namespace(Path(td).resolve(), lambda *a, **kw: sentinel)
            with patch.object(media, "capture_media_observation", side_effect=AssertionError("must not read")):
                exec(helper.block(), ns)
            self.assertIs(ns["witness"], sentinel)
            self.assertEqual(ns["phase"], {"phase": "REAL_GENERATED_CONSUMER", "layer_frames": 48, "render_passed": False})

    def test_new_file_assigned_once_all_historical_native_paths_retained(self):
        from tests.compiler import run_m1_tests as runner
        lanes, inherited = runner.inventory()
        path = "tests/compiler/test_m1_media_diagnostics.py"
        self.assertEqual(lanes["new"].count(path), 1)
        self.assertNotIn(path, lanes["native-extra"]); self.assertNotIn(path, lanes["safety"]); self.assertNotIn(path, inherited)
        self.assertEqual(len(lanes["native-extra"]), 214)


if __name__ == "__main__": unittest.main()
