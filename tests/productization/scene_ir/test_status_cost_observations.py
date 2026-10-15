"""Synthetic cost-observer controls, not native stage/renderer evidence."""
from copy import deepcopy
import json
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from bie.productization.scene_ir_slice import SceneIRProducerService, STAGES
from . import status_cost_observations as probe


class StatusCostControls(unittest.TestCase):
    def setUp(self):
        self.saved = dict(stages={s: dict(attempts=[dict(state="SUCCEEDED")]) for s in STAGES})
        self.queues = dict(ACKED=11, READY=0, DELIVERED=0, DEAD_LETTER=0)
        self.service = object.__new__(SceneIRProducerService)
        self.service.persistence = SimpleNamespace(load_run_state=lambda _: deepcopy(self.saved))
        self.service.queue = SimpleNamespace(stats=lambda: deepcopy(self.queues))
        self.record = SimpleNamespace(blob_digest="a"*64)
        self.value = dict(stages=dict.fromkeys(STAGES, "SUCCEEDED"))
        self.error = RuntimeError("PRIVATE token /private/book/path")

    def observe(self, action=None):
        with patch.object(self.service, "stage_ref", return_value=("artifact-identity", self.record)), \
             patch.object(self.service, "status", side_effect=action or (lambda *_: self.value)) as call:
            value = probe.observe(self.service, "exact-run", "exact-tenant", deepcopy(self.saved), deepcopy(self.queues))
        return value, call

    def test_exactly_one_status_read(self):
        value, call = self.observe()
        call.assert_called_once_with("exact-run", "exact-tenant")
        self.assertEqual(value["outcome"], "RETURNED")
        self.assertFalse(value["original_child_passed"])
        self.assertFalse(value["product_accepted"])

    def test_current_state_and_queue_conserved(self):
        value, _ = self.observe()
        self.assertTrue(value["state_unchanged"]); self.assertTrue(value["queue_unchanged"])
        self.assertTrue(value["profile_restored"])

    def test_exception_remains_non_success_without_message(self):
        value, call = self.observe(lambda *_: (_ for _ in ()).throw(self.error))
        self.assertEqual(value["outcome"], "RAISED")
        self.assertEqual(value["exception_class"], "RuntimeError")
        self.assertNotIn("PRIVATE", json.dumps(value))
        self.assertTrue(value["profile_restored"]); call.assert_called_once()

    def test_foreign_service_is_not_invoked(self):
        value = probe.observe(object(), "run", "tenant", self.saved, self.queues)
        self.assertEqual(value["outcome"], "NOT_ADMITTED")

    def test_partial_state_does_not_trigger_read(self):
        self.saved["stages"]["SCENE_IR"]["attempts"][-1]["state"] = "RUNNING"
        value, call = self.observe()
        call.assert_not_called(); self.assertEqual(value["outcome"], "NOT_ADMITTED")

    def test_nonterminal_queue_does_not_trigger_read(self):
        self.queues["READY"] = 1
        _, call = self.observe(); call.assert_not_called()

    def test_boolean_ack_is_not_eleven(self):
        self.queues["ACKED"] = True
        _, call = self.observe(); call.assert_not_called()

    def test_state_mutation_is_not_a_valid_observation(self):
        def mutate(*_):
            self.saved["stages"]["SCENE_IR"]["attempts"][-1]["attempt"] = 2
            return self.value
        value, _ = self.observe(mutate)
        self.assertEqual(value["outcome"], "STATE_CHANGED")
        self.assertFalse(value["state_unchanged"])

    def test_queue_mutation_is_detected(self):
        def mutate(*_):
            self.queues["ACKED"] = 10
            return self.value
        value, _ = self.observe(mutate)
        self.assertEqual(value["outcome"], "STATE_CHANGED")

    def test_foreign_reference_not_exported(self):
        self.record.blob_digest = "PRIVATE"
        value, call = self.observe()
        call.assert_not_called()
        self.assertEqual(value["outcome"], "UNAVAILABLE")
        self.assertNotIn("PRIVATE", json.dumps(value))

    def test_existing_profiler_is_not_replaced(self):
        prior = sys.getprofile()
        def listener(*_): pass
        try:
            sys.setprofile(listener)
            value, call = self.observe()
            call.assert_not_called()
            self.assertIs(sys.getprofile(), listener)
            self.assertEqual(value["outcome"], "NOT_ADMITTED")
        finally: sys.setprofile(prior)

    def test_stats_failure_cannot_escape_or_mint_pass(self):
        with patch.object(probe, "project_stats", side_effect=self.error):
            value, call = self.observe()
        call.assert_called_once()
        self.assertEqual(value["outcome"], "UNAVAILABLE")
        self.assertNotIn("PRIVATE", json.dumps(value))

    def test_profiler_construction_failure_is_not_reader_failure(self):
        with patch.object(probe.cProfile, "Profile", side_effect=self.error):
            value, call = self.observe()
        call.assert_not_called()
        self.assertFalse(value["reader_called"])
        self.assertEqual(value["outcome"], "UNAVAILABLE")

    def test_partial_enable_failure_restores_prior_binding(self):
        prior=sys.getprofile()
        def listener(*_):pass
        class Broken:
            def enable(self):
                sys.setprofile(listener);raise RuntimeError("PRIVATE")
            def disable(self):raise RuntimeError("PRIVATE")
        with patch.object(probe.cProfile,"Profile",return_value=Broken()):
            value,call=self.observe()
        call.assert_not_called();self.assertIs(sys.getprofile(),prior)
        self.assertTrue(value["profile_restored"]);self.assertFalse(value["observation_complete"])

    def test_disable_failure_restores_and_does_not_replace_reader_error(self):
        prior=sys.getprofile()
        def listener(*_):pass
        class Broken:
            def enable(self):sys.setprofile(listener)
            def disable(self):raise RuntimeError("PRIVATE observer")
            def getstats(self):return []
        with patch.object(probe.cProfile,"Profile",return_value=Broken()):
            value,call=self.observe(lambda *_: (_ for _ in ()).throw(ValueError("PRIVATE reader")))
        call.assert_called_once();self.assertIs(sys.getprofile(),prior)
        self.assertEqual(value["outcome"],"RAISED");self.assertEqual(value["exception_class"],"ValueError")
        self.assertTrue(value["profile_restored"]);self.assertFalse(value["observation_complete"])

    def test_tampered_reference_not_exported_before_reader_rejects(self):
        with patch.object(self.service,"stage_ref",return_value=("PRIVATE_SECRET",self.record)), \
             patch.object(self.service,"status",side_effect=self.error):
            value=probe.observe(self.service,"run","tenant",deepcopy(self.saved),deepcopy(self.queues))
        self.assertEqual(value["dependencies"],[])
        self.assertNotIn("PRIVATE_SECRET",json.dumps(value))

    def test_returned_reference_is_only_hash_bound(self):
        value,_=self.observe()
        self.assertTrue(value["dependencies"])
        self.assertNotIn("artifact-identity",json.dumps(value))
        self.assertEqual(set(value["dependencies"][0]),{"stage","reference_sha256","sha256"})

    def test_private_builtin_representation_never_requested(self):
        class Private:
            def __str__(self): raise AssertionError("not inspected")
            def __repr__(self): raise AssertionError("not inspected")
        value = probe.project_stats(SimpleNamespace(getstats=lambda: [SimpleNamespace(code=Private())]))
        self.assertEqual(value, [])

    def test_only_known_method_names_project(self):
        code = compile("def status(): pass", str(probe.ROOT/"bie/productization/scene_ir_slice.py"), "exec").co_consts[0]
        entry = SimpleNamespace(code=code, callcount=7, inlinetime=.001, totaltime=.002)
        rows = probe.project_stats(SimpleNamespace(getstats=lambda: [entry]))
        self.assertEqual(rows, [dict(source="bie/productization/scene_ir_slice.py", function="status",
            calls=7, exclusive_cpu_ms=1, cumulative_cpu_ms=2)])

    def test_foreign_path_not_exported(self):
        code = compile("def status(): pass", str(probe.ROOT.parent/"PRIVATE.py"), "exec").co_consts[0]
        self.assertEqual(probe.project_stats(SimpleNamespace(getstats=lambda: [SimpleNamespace(code=code)])), [])

    def test_boolean_or_nonfinite_timings_are_unknown(self):
        for value in (True, False, float("nan"), float("inf"), -1, 121, "PRIVATE"):
            self.assertIsNone(probe.milliseconds(value))
        self.assertEqual(probe.milliseconds(0), 0)

    def test_invalid_call_count_is_rejected(self):
        code = compile("def status(): pass", str(probe.ROOT/"bie/productization/scene_ir_slice.py"), "exec").co_consts[0]
        for count in (True, -1, 0, 1000001, "PRIVATE"):
            entry = SimpleNamespace(code=code, callcount=count, inlinetime=0, totaltime=0)
            with self.assertRaises(ValueError):
                probe.project_stats(SimpleNamespace(getstats=lambda: [entry]))

    def test_duplicate_method_rows_are_rejected(self):
        code = compile("def status(): pass", str(probe.ROOT/"bie/productization/scene_ir_slice.py"), "exec").co_consts[0]
        entry = SimpleNamespace(code=code, callcount=1, inlinetime=0, totaltime=0)
        with self.assertRaises(ValueError):
            probe.project_stats(SimpleNamespace(getstats=lambda: [entry, entry]))

    def test_oversized_stats_are_rejected(self):
        with self.assertRaises(ValueError):
            probe.project_stats(SimpleNamespace(getstats=lambda: [None]*8193))

    def test_closed_root_shape_and_private_payload_absent(self):
        self.value["PRIVATE"] = dict(stderr="secret", argv=["/private/path"], source="book text")
        value, _ = self.observe()
        self.assertEqual(set(value), {"schema", "scope", "outcome", "exception_class", "cpu_ms",
            "methods", "dependencies", "state_unchanged", "queue_unchanged", "profile_restored",
            "reader_called", "observation_complete", "original_child_passed", "product_accepted"})
        for text in ("PRIVATE", "stderr", "argv", "/private/path", "book text"):
            self.assertNotIn(text, json.dumps(value))


if __name__ == "__main__": unittest.main()
