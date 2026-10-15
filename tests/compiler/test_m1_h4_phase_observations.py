"""Pure delegation/privacy controls, not a passing H4/native browser fixture."""
import gc
import json
from pathlib import Path
import unittest
from unittest.mock import patch
import weakref

from . import m1_h4_phase_observations as probe


class H4PhaseControls(unittest.TestCase):
    def test_exact_once_and_argument_identity(self):
        state=probe.new_state(); calls=[]; arg=object(); keyword=object(); result=object()
        def original(*args,**kwargs):
            calls.append((args,kwargs)); return result
        value=probe.wrapper(original,"CANDIDATES",state)(arg, private=keyword)
        self.assertIs(value,result);self.assertEqual(len(calls),1)
        self.assertIs(calls[0][0][0],arg);self.assertIs(calls[0][1]["private"],keyword)
        self.assertEqual(state["phases"]["CANDIDATES"],dict(calls=1,returned=1,raised=0))

    def test_original_exception_identity(self):
        error=PermissionError("PRIVATE stderr and source")
        state=probe.new_state()
        def original():raise error
        with self.assertRaises(PermissionError) as caught:probe.wrapper(original,"PROBE_ENTER",state)()
        self.assertIs(caught.exception,error)
        self.assertEqual(state["exceptions"],[dict(phase="PROBE_ENTER",exception_class="PermissionError",structured_code="UNKNOWN")])
        self.assertNotIn("PRIVATE",json.dumps(probe.snapshot(state)))

    def test_base_exception_identity(self):
        error=KeyboardInterrupt();state=probe.new_state()
        def original():raise error
        with self.assertRaises(KeyboardInterrupt) as caught:probe.wrapper(original,"CANDIDATES",state)()
        self.assertIs(caught.exception,error);self.assertEqual(state["exceptions"][0]["exception_class"],"UNKNOWN")

    def test_observer_error_does_not_mask_native_error(self):
        error=ValueError("PRIVATE");state=probe.new_state()
        def original():raise error
        with patch.object(probe,"note",side_effect=RuntimeError("PRIVATE observer")):
            with self.assertRaises(ValueError) as caught:probe.wrapper(original,"PROBE_EXIT",state)()
        self.assertIs(caught.exception,error);self.assertFalse(state["complete"])

    def test_observer_error_does_not_replace_return(self):
        state=probe.new_state();value=object()
        with patch.object(probe,"note",side_effect=RuntimeError("PRIVATE")):
            self.assertIs(probe.wrapper(lambda:value,"PROBE_EXIT",state)(),value)
        self.assertFalse(state["complete"])

    def test_private_objects_not_retained(self):
        class Private:pass
        state=probe.new_state();value=Private();ref=weakref.ref(value)
        delegated=probe.wrapper(lambda _:None,"CANDIDATES",state)
        delegated(value);del value;gc.collect()
        self.assertIsNone(ref())

    def test_private_messages_never_formatted(self):
        class PrivateError(ValueError):
            def __str__(self):raise AssertionError()
            def __repr__(self):raise AssertionError()
        state=probe.new_state()
        def original():raise PrivateError()
        with self.assertRaises(PrivateError):probe.wrapper(original,"PROBE_CONSTRUCT",state)()
        self.assertEqual(state["exceptions"][0]["exception_class"],"UNKNOWN")

    def test_actual_bindings_restored_without_execution(self):
        from bie.compiler import layout_repair
        from bie.compiler.layout_browser import ChromiumLayoutProbe
        before=(layout_repair._run_candidates,ChromiumLayoutProbe.__enter__,ChromiumLayoutProbe.__exit__)
        with probe.capture() as state:
            self.assertTrue(state["available"])
            self.assertIsNot(layout_repair._run_candidates,before[0])
        self.assertEqual((layout_repair._run_candidates,ChromiumLayoutProbe.__enter__,ChromiumLayoutProbe.__exit__),before)
        self.assertTrue(state["bindings_restored"])

    def test_native_exception_through_context_preserved(self):
        from bie.compiler import layout_repair
        before=layout_repair._run_candidates;error=RuntimeError("PRIVATE")
        with self.assertRaises(RuntimeError) as caught:
            with probe.capture() as state:raise error
        self.assertIs(caught.exception,error);self.assertIs(layout_repair._run_candidates,before)
        self.assertTrue(state["bindings_restored"])

    def test_foreign_root_does_not_patch(self):
        from bie.compiler import layout_repair
        before=layout_repair._run_candidates
        with probe.capture(probe.ROOT.parent) as state:
            self.assertFalse(state["available"]);self.assertFalse(state["complete"])
            self.assertIs(layout_repair._run_candidates,before)

    def test_context_close_error_is_contained_and_original_restored(self):
        from types import SimpleNamespace
        original=lambda:None
        owner=SimpleNamespace(method=lambda:False)
        class FailedClose:
            def close(self):raise RuntimeError("PRIVATE")
        state=probe.new_state()
        probe.restore(FailedClose(),[(owner,"method",original)],state)
        self.assertIs(owner.method,original)
        self.assertTrue(state["bindings_restored"]);self.assertFalse(state["complete"])

    def test_counter_boundary_is_bounded(self):
        state=probe.new_state()
        for _ in range(65):probe.note(state,"CANDIDATES","CALL")
        self.assertEqual(state["phases"]["CANDIDATES"]["calls"],64);self.assertFalse(state["complete"])

    def test_exception_rows_bounded(self):
        state=probe.new_state()
        for _ in range(9):probe.note(state,"PROBE_ENTER","RAISE",ValueError("PRIVATE"))
        self.assertEqual(len(state["exceptions"]),8);self.assertFalse(state["complete"])

    def test_boolean_counter_rejected(self):
        state=probe.new_state();state["phases"]["CANDIDATES"]["calls"]=True
        self.assertFalse(probe.snapshot(state)["complete"])

    def test_unknown_exception_class_not_exported(self):
        state=probe.new_state();state["exceptions"]=[dict(phase="CANDIDATES",exception_class="PRIVATE",structured_code="UNKNOWN")]
        value=probe.snapshot(state)
        self.assertFalse(value["complete"]);self.assertNotIn("PRIVATE",json.dumps(value))

    def test_no_unverified_code_classification(self):
        state=probe.new_state();state["exceptions"]=[dict(phase="CANDIDATES",exception_class="ValueError",structured_code="TIMEOUT")]
        self.assertFalse(probe.snapshot(state)["complete"])

    def test_no_acceptance_promotion(self):
        state=probe.new_state();state["accepted"]=True
        value=probe.snapshot(state)
        self.assertFalse(value["accepted"]);self.assertFalse(value["complete"])

    def test_closed_shape_and_unknown_fields_not_copied(self):
        state=probe.new_state();state["stderr"]="PRIVATE";state["argv"]=["/private/path"]
        value=probe.snapshot(state)
        self.assertEqual(set(value),{"schema","available","complete","bindings_restored","phases","exceptions","accepted","product_accepted"})
        self.assertNotIn("PRIVATE",json.dumps(value));self.assertNotIn("argv",json.dumps(value))

    def test_registered_once_without_native_inventory_growth(self):
        from .run_m1_tests import inventory
        selected,inherited=inventory();name="tests/compiler/test_m1_h4_phase_observations.py"
        self.assertEqual(selected["new"].count(name),1)
        self.assertNotIn(name,selected["native-extra"]);self.assertNotIn(name,selected["safety"]);self.assertNotIn(name,inherited)
        self.assertEqual(len(selected["native-extra"]),214)


if __name__=="__main__":unittest.main()
