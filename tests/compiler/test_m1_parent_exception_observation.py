"""Synthetic observer contracts, not Linux renderer or product acceptance."""
import gc
from hashlib import sha256
import json
from pathlib import Path
import sys
import threading
from types import CodeType
import unittest
from unittest.mock import patch
import weakref

from tests.compiler import m1_parent_exception_observation as d


def synthetic():
    namespace = {}
    exec(compile("def run_chromium_isolated(callback):\n    return callback()\n"
        "def bounded_read(callback):\n    return callback()\n", "<synthetic-parent>", "exec"), namespace)
    return namespace["run_chromium_isolated"], namespace["bounded_read"]


class ParentExceptionObservation(unittest.TestCase):
    def setUp(self):
        self.previous = sys.gettrace()
        self.run, self.read = synthetic()
        self.targets = ((self.run.__code__, "run_chromium_isolated", self.run.__globals__),
            (self.read.__code__, "bounded_read", self.read.__globals__))

    def tearDown(self):
        self.assertIs(sys.gettrace(), self.previous)

    def scope(self):
        return patch.object(d, "canonical_targets", return_value=self.targets)

    def raised(self, error):
        def callback(): raise error
        return callback

    def test_identical_return_and_exactly_once_delegate(self):
        token = object(); calls = []
        def callback(): calls.append(token); return token
        with self.scope(), d.observe_parent_exception_sites() as observer:
            self.assertIs(self.run(callback), token)
        self.assertEqual(calls, [token])
        self.assertEqual(observer.snapshot()["selected_exception_events"], 0)
        self.assertTrue(observer.snapshot()["binding_restored"])

    def test_original_exception_identity_and_single_execution(self):
        original = PermissionError("PRIVATE token /private/book")
        calls = []
        def callback(): calls.append(1); raise original
        with self.scope():
            with self.assertRaises(PermissionError) as caught:
                with d.observe_parent_exception_sites() as observer: self.run(callback)
        self.assertIs(caught.exception, original)
        self.assertEqual(calls, [1])
        self.assertEqual(observer.snapshot()["first_site"], "RUN_OTHER")

    def test_handled_event_is_not_a_final_cause_or_verdict(self):
        with self.scope(), d.observe_parent_exception_sites() as observer:
            try: self.run(self.raised(PermissionError("PRIVATE")))
            except PermissionError: pass
        safe = observer.snapshot()
        self.assertEqual(safe["selected_exception_events"], 1)
        self.assertEqual(safe["scope"], "OBSERVED_EVENTS_NOT_FINAL_CAUSE_OR_PROCESS_VERDICT")
        self.assertFalse(safe["render_passed"])

    def test_propagation_first_and_last_are_distinct_observations(self):
        with self.scope():
            with self.assertRaises(PermissionError):
                with d.observe_parent_exception_sites() as observer:
                    self.run(lambda: self.read(self.raised(PermissionError("PRIVATE"))))
        safe = observer.snapshot()
        self.assertEqual(safe["selected_exception_events"], 2)
        self.assertEqual(safe["first_site"], "BOUNDED_READ_OTHER")
        self.assertEqual(safe["last_site"], "RUN_OTHER")

    def test_other_exception_not_inferred_as_permission(self):
        with self.scope():
            with self.assertRaises(OSError):
                with d.observe_parent_exception_sites() as observer: self.run(self.raised(OSError("PRIVATE")))
        self.assertEqual(observer.snapshot()["selected_exception_events"], 0)

    def test_permission_subclass_is_not_exact_builtin_evidence(self):
        class Foreign(PermissionError): pass
        with self.scope():
            with self.assertRaises(Foreign):
                with d.observe_parent_exception_sites() as observer: self.run(self.raised(Foreign("PRIVATE")))
        self.assertEqual(observer.snapshot()["first_site"], d.UNKNOWN)

    def test_only_pinned_code_objects_are_observed(self):
        def foreign(): raise PermissionError("PRIVATE")
        with self.scope():
            with self.assertRaises(PermissionError):
                with d.observe_parent_exception_sites() as observer: foreign()
        self.assertEqual(observer.snapshot()["selected_exception_events"], 0)

    def test_same_function_name_foreign_code_not_observed(self):
        other, _ = synthetic()
        # A different code identity is rejected even when the code is equal.
        self.assertIsNot(other.__code__, self.run.__code__)
        with self.scope():
            with self.assertRaises(PermissionError):
                with d.observe_parent_exception_sites() as observer: other(self.raised(PermissionError()))
        self.assertEqual(observer.snapshot()["selected_exception_events"], 0)

    def test_existing_tracer_is_never_replaced(self):
        def previous(frame, event, arg): return None
        sys.settrace(previous)
        try:
            with self.scope(), d.observe_parent_exception_sites() as observer:
                self.assertIs(sys.gettrace(), previous)
                self.assertEqual(self.run(lambda: 7), 7)
            self.assertIs(sys.gettrace(), previous)
            self.assertEqual(observer.snapshot()["reason"], "EXISTING_TRACER")
        finally: sys.settrace(self.previous)

    def test_nested_scope_declines_without_disturbing_outer(self):
        with self.scope(), d.observe_parent_exception_sites() as outer:
            tracer = sys.gettrace()
            with d.observe_parent_exception_sites() as inner: self.assertIs(sys.gettrace(), tracer)
            self.assertEqual(inner.snapshot()["reason"], "EXISTING_TRACER")
        self.assertTrue(outer.snapshot()["binding_restored"])

    def test_setup_fault_cannot_mask_delegate(self):
        with self.scope(), patch.object(d.sys, "settrace", side_effect=RuntimeError("PRIVATE")):
            with d.observe_parent_exception_sites() as observer: self.assertEqual(self.run(lambda: 7), 7)
        self.assertEqual(observer.snapshot()["reason"], "SETUP_FAILED")

    def test_binding_failure_leaves_call_unchanged(self):
        with patch.object(d, "canonical_targets", side_effect=ValueError("PRIVATE")):
            with d.observe_parent_exception_sites() as observer: self.assertEqual(self.run(lambda: 8), 8)
        self.assertEqual(observer.snapshot()["reason"], "SOURCE_UNAVAILABLE")

    def test_partial_setup_failure_restores_only_our_binding(self):
        original = sys.settrace
        def setter(callback):
            original(callback)
            if callback is not None: raise RuntimeError("PRIVATE")
        with self.scope(), patch.object(d.sys, "settrace", side_effect=setter):
            with d.observe_parent_exception_sites() as observer:
                self.assertEqual(self.run(lambda: 9), 9)
        safe = observer.snapshot()
        self.assertEqual(safe["reason"], "SETUP_FAILED")
        self.assertTrue(safe["binding_restored"])

    def test_callback_fault_cannot_replace_original_exception(self):
        error = PermissionError("PRIVATE")
        with self.scope():
            with self.assertRaises(PermissionError) as caught:
                with d.observe_parent_exception_sites() as observer:
                    observer._safe = None
                    self.run(self.raised(error))
        self.assertIs(caught.exception, error)
        self.assertEqual(observer.snapshot()["availability"], "UNAVAILABLE")

    def test_constructor_fault_cannot_preempt_original_delegate(self):
        original = PermissionError("PRIVATE"); calls = []
        def callback(): calls.append(1); raise original
        with patch.object(d, "ExceptionSiteObserver", side_effect=RuntimeError("PRIVATE")):
            with self.assertRaises(PermissionError) as caught:
                with d.observe_parent_exception_sites() as observer: self.run(callback)
        self.assertIsNone(observer)
        self.assertIs(caught.exception, original)
        self.assertEqual(calls, [1])

    def test_restoration_bookkeeping_fault_cannot_mask_original_rejection(self):
        original = PermissionError("PRIVATE")
        with self.scope():
            with self.assertRaises(PermissionError) as caught:
                with d.observe_parent_exception_sites() as observer:
                    try: self.run(self.raised(original))
                    finally: observer._safe = None
        self.assertIs(caught.exception, original)
        self.assertIs(sys.gettrace(), self.previous)

    def test_foreign_tracer_installed_during_call_is_not_overwritten(self):
        def foreign(frame, event, arg): return None
        try:
            with self.scope(), d.observe_parent_exception_sites() as observer:
                sys.settrace(foreign)
            self.assertIs(sys.gettrace(), foreign)
            self.assertEqual(observer.snapshot()["reason"], "RESTORATION_CHANGED")
            self.assertFalse(observer.snapshot()["binding_restored"])
        finally: sys.settrace(self.previous)

    def test_restoration_fault_does_not_mask_original_rejection(self):
        real_set = sys.settrace; calls = []
        def setter(value):
            calls.append(value is None)
            if value is None: raise RuntimeError("PRIVATE")
            return real_set(value)
        original = PermissionError("PRIVATE")
        try:
            with self.scope(), patch.object(d.sys, "settrace", side_effect=setter):
                with self.assertRaises(PermissionError) as caught:
                    with d.observe_parent_exception_sites() as observer: self.run(self.raised(original))
            self.assertIs(caught.exception, original)
            self.assertEqual(observer.snapshot()["reason"], "RESTORATION_FAILED")
        finally: real_set(self.previous)

    def test_event_count_and_retained_state_are_bounded(self):
        with self.scope(), d.observe_parent_exception_sites() as observer:
            for _ in range(100):
                try: self.run(self.raised(PermissionError("PRIVATE")))
                except PermissionError: pass
        self.assertEqual(observer.snapshot()["selected_exception_events"], d.MAX_EVENTS)
        self.assertTrue(observer.snapshot()["event_limit_reached"])

    def test_private_value_stringification_is_never_used(self):
        class Private:
            def __str__(self): raise AssertionError("PRIVATE_STR")
            def __repr__(self): raise AssertionError("PRIVATE_REPR")
        error = PermissionError(Private())
        with self.scope():
            with self.assertRaises(PermissionError):
                with d.observe_parent_exception_sites() as observer: self.run(self.raised(error))
        safe = json.dumps(observer.snapshot())
        self.assertNotIn("PRIVATE", safe)

    def test_exception_payload_and_traceback_not_retained(self):
        class Private: pass
        token = Private(); reference = weakref.ref(token)
        with self.scope(), d.observe_parent_exception_sites() as observer:
            try: self.run(self.raised(PermissionError(token)))
            except PermissionError: pass
        del token; gc.collect()
        self.assertIsNone(reference())
        self.assertTrue(d.is_safe_observation(observer.snapshot()))

    def test_large_private_args_have_no_safe_surface(self):
        original = PermissionError("SECRET_TOKEN PRIVATE_BOOK /private/path " * 100000)
        with self.scope():
            with self.assertRaises(PermissionError):
                with d.observe_parent_exception_sites() as observer: self.run(self.raised(original))
        encoded = json.dumps(observer.snapshot())
        self.assertLess(len(encoded), 2048)
        for value in ("SECRET_TOKEN", "PRIVATE_BOOK", "/private/path"): self.assertNotIn(value, encoded)

    def test_current_thread_scope_does_not_instrument_another_thread(self):
        seen = []
        with self.scope(), d.observe_parent_exception_sites() as observer:
            thread = threading.Thread(target=lambda: seen.append(sys.gettrace()))
            thread.start(); thread.join()
        self.assertEqual(seen, [None])
        self.assertTrue(observer.snapshot()["binding_restored"])

    def test_unavailable_is_not_zero_false_or_success(self):
        safe = d.empty_observation()
        self.assertEqual(safe["selected_exception_events"], d.UNKNOWN)
        self.assertEqual(safe["binding_restored"], d.UNKNOWN)
        self.assertFalse(safe["render_passed"])
        self.assertTrue(d.is_safe_observation(safe))

    def test_unknown_scalars_cannot_be_counterfeit_equal_objects(self):
        class Counterfeit:
            def __eq__(self, other): return True
            def __ne__(self, other): return False
        for field in ("binding_restored", "selected_exception_events", "event_limit_reached"):
            safe = d.empty_observation(); safe[field] = Counterfeit()
            self.assertFalse(d.is_safe_observation(safe))

    def test_line_and_opcode_events_are_disabled_on_selected_frames(self):
        def flags():
            frame = sys._getframe(1)
            return frame.f_trace_lines, frame.f_trace_opcodes
        with self.scope(), d.observe_parent_exception_sites():
            self.assertEqual(self.run(flags), (False, False))

    def test_delegate_cleanup_occurs_before_original_exception_escapes(self):
        import tempfile
        saved = []
        original = PermissionError("PRIVATE")
        def callback():
            with tempfile.TemporaryDirectory() as folder:
                saved.append(Path(folder)); raise original
        with self.scope():
            with self.assertRaises(PermissionError) as caught:
                with d.observe_parent_exception_sites(): self.run(callback)
        self.assertIs(caught.exception, original)
        self.assertFalse(saved[0].exists())

    def test_source_location_contracts_match_pinned_public_lines(self):
        # Preserve every original line assertion against the immutable actual
        # preimage; version-2 live sites have separate exact source-pin checks.
        source = (Path(__file__).resolve().parents[2]/"docs/productization/task036-monitor-snapshot-amendment/chromium_resource_worker.py.before").read_text().splitlines()
        self.assertIn("os.readlink(proc/'exe'),os.readlink(proc/'root')", source[359])
        self.assertIn("resource.prlimit(pid", source[361])
        self.assertIn("bounded_read(proc/'maps'", source[362])
        self.assertIn("open('xb')", source[411])
        self.assertEqual(d.LOCATIONS["bounded_read"][76], "BOUNDED_READ_OPEN_OR_READ")
        self.assertEqual(d.DEFAULTS["bounded_read"], "BOUNDED_READ_OTHER")

    def test_closed_schema_rejects_unknown_keys(self):
        safe = d.empty_observation(); safe["stderr"] = "PRIVATE"
        self.assertFalse(d.is_safe_observation(safe))

    def test_schema_pin_and_enum_tamper_rejected(self):
        for field, value in (("schema", "forged"), ("source_sha256", "0"*64), ("first_site", "PRIVATE"),
                ("availability", "SUCCESS"), ("exception_kind", "OSError"), ("reason", "PRIVATE")):
            safe = d.empty_observation(); safe[field] = value
            self.assertFalse(d.is_safe_observation(safe), field)

    def test_counter_bool_negative_overflow_rejected(self):
        with self.scope(), d.observe_parent_exception_sites() as observer: pass
        for value in (True, -1, 33, 1.0, float("nan")):
            safe = observer.snapshot(); safe["selected_exception_events"] = value
            self.assertFalse(d.is_safe_observation(safe))

    def test_no_acceptance_promotion(self):
        for field in ("render_passed", "accepted", "product_accepted"):
            safe = d.empty_observation(); safe[field] = True
            self.assertFalse(d.is_safe_observation(safe))

    def test_link_site_does_not_claim_which_subexpression(self):
        self.assertEqual(d.LEGACY_LOCATIONS["run_chromium_isolated"][360], "MONITOR_EXE_OR_ROOT_LINK")

    def test_exact_canonical_source_and_function_binding(self):
        path = Path(__file__).resolve().parents[2]/"bie/compiler/chromium_resource_worker.py"
        self.assertEqual(sha256(path.read_bytes()).hexdigest(), d.SOURCE_SHA256)
        targets = d.canonical_targets()
        self.assertEqual({name for _, name, _ in targets}, set(d.LOCATIONS))
        self.assertTrue(all(type(code) is CodeType for code, _, _ in targets))

    def test_foreign_function_with_canonical_filename_rejected(self):
        from bie.compiler import chromium_resource_worker as worker
        with patch.object(worker, "bounded_read", lambda *args: None):
            with self.assertRaises(ValueError): d.canonical_targets()

    def test_copied_canonical_code_with_foreign_namespace_rejected(self):
        from types import FunctionType
        from bie.compiler import chromium_resource_worker as worker
        original = worker.bounded_read
        foreign = FunctionType(original.__code__, {"__name__": worker.__name__}, original.__name__)
        self.assertEqual(foreign.__code__, original.__code__)
        with patch.object(worker, "bounded_read", foreign):
            with self.assertRaises(ValueError): d.canonical_targets()

    def test_optional_wrapper_import_failure_preserves_original_painter(self):
        import builtins
        import tempfile
        from tests.compiler.test_m1_safe_paint_diagnostics import TypedWrapperRetention
        original_import = builtins.__import__; calls = []
        token = object()
        def painter(*args, **kwargs): calls.append(1); return token
        def import_guard(name, *args, **kwargs):
            if name == "tests.compiler.m1_parent_exception_observation": raise ImportError("PRIVATE")
            return original_import(name, *args, **kwargs)
        with tempfile.TemporaryDirectory() as temp:
            helper = TypedWrapperRetention(); ns = helper.namespace(Path(temp).resolve(), painter)
            with patch.object(builtins, "__import__", side_effect=import_guard): exec(helper.block(), ns)
        self.assertIs(ns["witness"], token)
        self.assertEqual(calls, [1])
        self.assertNotIn("paint_parent_exception_observation", ns["phase"])

    def test_optional_wrapper_factory_failure_preserves_original_painter_rejection(self):
        import tempfile
        from bie.compiler.qa_common import CompilerQAError
        from tests.compiler.test_m1_safe_paint_diagnostics import TypedWrapperRetention
        original = CompilerQAError("ACTUAL_PAINT_EXECUTION_BLOCKED:PRIVATE"); calls = []
        def painter(*args, **kwargs): calls.append(1); raise original
        with tempfile.TemporaryDirectory() as temp:
            helper = TypedWrapperRetention(); ns = helper.namespace(Path(temp).resolve(), painter)
            with patch.object(d, "observe_parent_exception_sites", side_effect=RuntimeError("PRIVATE")):
                with self.assertRaises(CompilerQAError) as caught: exec(helper.block(), ns)
        self.assertIs(caught.exception, original)
        self.assertEqual(calls, [1])
        self.assertFalse(ns["phase"]["render_passed"])
        self.assertNotIn("paint_parent_exception_observation", ns["phase"])

    def test_optional_wrapper_constructor_failure_still_calls_native_once(self):
        import tempfile
        from tests.compiler.test_m1_safe_paint_diagnostics import TypedWrapperRetention
        token = object(); calls = []
        def painter(*args, **kwargs): calls.append(1); return token
        with tempfile.TemporaryDirectory() as temp:
            helper = TypedWrapperRetention(); ns = helper.namespace(Path(temp).resolve(), painter)
            with patch.object(d, "ExceptionSiteObserver", side_effect=RuntimeError("PRIVATE")): exec(helper.block(), ns)
        self.assertIs(ns["witness"], token)
        self.assertEqual(calls, [1])

    def test_failure_snapshot_rejects_private_extra_fields(self):
        import tempfile
        from contextlib import contextmanager
        from bie.compiler.qa_common import CompilerQAError
        from tests.compiler.test_m1_safe_paint_diagnostics import TypedWrapperRetention
        class Broken:
            def snapshot(self): return {"stderr": "PRIVATE_TOKEN /private/book"}
        @contextmanager
        def factory(): yield Broken()
        original = CompilerQAError("ACTUAL_PAINT_EXECUTION_BLOCKED:PRIVATE")
        with tempfile.TemporaryDirectory() as temp:
            helper = TypedWrapperRetention(); ns = helper.namespace(Path(temp).resolve(), self.raised(original))
            # Painter receives canonical call arguments, unlike the no-arg test callback.
            ns["produce_actual_paint"] = lambda *a, **k: self.raised(original)()
            with patch.object(d, "observe_parent_exception_sites", factory):
                with self.assertRaises(CompilerQAError) as caught: exec(helper.block(), ns)
        self.assertIs(caught.exception, original)
        self.assertNotIn("paint_parent_exception_observation", ns["phase"])
        self.assertNotIn("PRIVATE_TOKEN", json.dumps(ns["phase"]))

    def test_source_hash_mismatch_is_unavailable_not_admission(self):
        with patch.object(d, "SOURCE_SHA256", "0"*64):
            with d.observe_parent_exception_sites() as observer: self.assertEqual(self.run(lambda: 2), 2)
        self.assertEqual(observer.snapshot()["availability"], "UNAVAILABLE")

    def test_inventory_registered_once_without_native_extra_overlap(self):
        from tests.compiler import run_m1_tests as runner
        selected, inherited = runner.inventory()
        path = "tests/compiler/test_m1_parent_exception_observation.py"
        self.assertEqual(selected["new"].count(path), 1)
        self.assertNotIn(path, selected["native-extra"])
        self.assertNotIn(path, selected["safety"])
        self.assertNotIn(path, inherited)
        self.assertEqual(len(selected["native-extra"]), 214)

    def test_actual_wrapper_authenticates_before_typed_binding_replacement(self):
        import tempfile
        from contextlib import contextmanager
        from bie.compiler import chromium_resource_worker as worker
        from tests.compiler.test_m1_safe_paint_diagnostics import TypedWrapperRetention
        original = worker.run_chromium_isolated; prior = sys.gettrace()
        observed = []; factory = d.observe_parent_exception_sites; token = object(); calls = []
        @contextmanager
        def checked():
            with factory() as observer:
                observed.append(observer)
                self.assertEqual(observer.snapshot()["availability"], "VALID")
                yield observer
        def painter(*args, **kwargs): calls.append(1); return token
        with tempfile.TemporaryDirectory() as temp:
            helper = TypedWrapperRetention(); ns = helper.namespace(Path(temp).resolve(), painter)
            with patch.object(d, "observe_parent_exception_sites", checked): exec(helper.block(), ns)
        self.assertIs(ns["witness"], token); self.assertEqual(calls, [1])
        self.assertTrue(observed[0].snapshot()["binding_restored"])
        self.assertIs(worker.run_chromium_isolated, original); self.assertIs(sys.gettrace(), prior)

    def test_actual_wrapper_failure_snapshot_follows_binding_restoration(self):
        import tempfile
        from bie.compiler import chromium_resource_worker as worker
        from bie.compiler.qa_common import CompilerQAError
        from tests.compiler.test_m1_safe_paint_diagnostics import TypedWrapperRetention
        original = worker.run_chromium_isolated; prior = sys.gettrace(); calls = []
        failure = CompilerQAError("ACTUAL_PAINT_EXECUTION_BLOCKED:PRIVATE")
        def painter(*args, **kwargs): calls.append(1); raise failure
        with tempfile.TemporaryDirectory() as temp:
            helper = TypedWrapperRetention(); ns = helper.namespace(Path(temp).resolve(), painter)
            with self.assertRaises(CompilerQAError) as caught: exec(helper.block(), ns)
        self.assertIs(caught.exception, failure); self.assertEqual(calls, [1])
        safe = ns["phase"]["paint_parent_exception_observation"]
        self.assertEqual(safe["availability"], "VALID"); self.assertTrue(safe["binding_restored"])
        self.assertIs(worker.run_chromium_isolated, original); self.assertIs(sys.gettrace(), prior)
        self.assertNotIn("PRIVATE", json.dumps(ns["phase"]))


if __name__ == "__main__": unittest.main()
