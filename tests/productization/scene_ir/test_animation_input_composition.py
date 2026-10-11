"""Pure fresh-operation reuse controls, not substitute native artifact proof."""
import ast
from pathlib import Path
import unittest
from unittest.mock import patch

from bie.productization.animation_slice import AnimationProducerService
from bie.productization.scene_ir_slice import SceneIRProducerService, _ANIMATION_INPUT_CAPTURE
from bie.productization.contracts import ProducerError


class AnimationInputCompositionControls(unittest.TestCase):
    def setUp(self):
        self.service = object.__new__(SceneIRProducerService)
        self.plan, self.receipt, self.bundle, self.ref = {}, {"sync_ref": {}}, {"private": "synthetic"}, object()

    def verify(self, service, run, tenant):
        value = service.animation_inputs(run, tenant, sync_ref=self.ref)
        self.assertIs(value, self.bundle)
        return self.plan, self.receipt

    def execute(self, side_effect=None):
        with patch.object(AnimationProducerService, "animation_inputs", return_value=self.bundle) as inputs, \
             patch.object(AnimationProducerService, "verified_animation", autospec=True,
                side_effect=side_effect or self.verify) as verified:
            result = self.service.verified_animation_with_inputs("run", "tenant")
        return result, inputs, verified

    def test_reuses_exact_native_consumed_objects_once(self):
        result, inputs, verified = self.execute()
        self.assertTrue(all(a is b for a, b in zip(result, (self.plan, self.receipt, self.bundle))))
        inputs.assert_called_once_with("run", "tenant", publish=False, sync_ref=self.ref)
        verified.assert_called_once_with(self.service, "run", "tenant")

    def test_each_call_executes_fresh_native_verification(self):
        first, _, _ = self.execute()
        self.bundle = {"new_revision": True}
        second, _, _ = self.execute()
        self.assertIsNot(first[2], second[2])

    def test_no_bundle_retained_on_service_or_context(self):
        self.execute()
        self.assertIsNone(_ANIMATION_INPUT_CAPTURE.get())
        self.assertEqual(vars(self.service), {})

    def test_native_rejection_identity_preserved_and_context_restored(self):
        error = RuntimeError("synthetic native rejection")
        with self.assertRaises(RuntimeError) as caught:
            self.execute(lambda *args: (_ for _ in ()).throw(error))
        self.assertIs(caught.exception, error)
        self.assertIsNone(_ANIMATION_INPUT_CAPTURE.get())

    def test_missing_native_input_call_fails_closed(self):
        with self.assertRaisesRegex(ProducerError, "scene_ir_animation_capture_cardinality"):
            self.execute(lambda *args: (self.plan, self.receipt))
        self.assertIsNone(_ANIMATION_INPUT_CAPTURE.get())

    def test_duplicate_native_input_call_fails_closed(self):
        def duplicate(service, run, tenant):
            self.verify(service, run, tenant)
            return self.verify(service, run, tenant)
        with self.assertRaisesRegex(ProducerError, "scene_ir_animation_capture_cardinality"):
            self.execute(duplicate)

    def test_foreign_run_or_tenant_rejected(self):
        for run, tenant in (("foreign", "tenant"), ("run", "foreign")):
            with self.subTest(run=run, tenant=tenant):
                with self.assertRaisesRegex(ProducerError, "scene_ir_animation_capture_scope"):
                    self.execute(lambda service, *_: (service.animation_inputs(run, tenant, sync_ref=self.ref), {}))

    def test_publication_cannot_be_used_as_verified_capture(self):
        with self.assertRaisesRegex(ProducerError, "scene_ir_animation_capture_scope"):
            self.execute(lambda service, run, tenant: (service.animation_inputs(run, tenant,
                publish=True, sync_ref=self.ref), {}))

    def test_absent_sync_reference_rejected(self):
        with self.assertRaisesRegex(ProducerError, "scene_ir_animation_capture_scope"):
            self.execute(lambda service, run, tenant: (service.animation_inputs(run, tenant), {}))

    def test_invalid_scope_rejected_before_native_read_or_publication(self):
        token = _ANIMATION_INPUT_CAPTURE.set(dict(service=self.service, run="run", tenant="tenant", bundles=[]))
        try:
            with patch.object(AnimationProducerService, "animation_inputs") as native:
                with self.assertRaisesRegex(ProducerError, "scene_ir_animation_capture_scope"):
                    self.service.animation_inputs("run", "tenant", publish=True, sync_ref=self.ref)
                native.assert_not_called()
        finally:
            _ANIMATION_INPUT_CAPTURE.reset(token)

    def test_nested_context_restored_not_retained(self):
        sentinel = {"outer": True}
        token = _ANIMATION_INPUT_CAPTURE.set(sentinel)
        try:
            self.execute()
            self.assertIs(_ANIMATION_INPUT_CAPTURE.get(), sentinel)
        finally:
            _ANIMATION_INPUT_CAPTURE.reset(token)

    def test_ordinary_animation_input_dispatch_unchanged_outside_scope(self):
        with patch.object(AnimationProducerService, "animation_inputs", return_value=self.bundle) as inputs:
            value = self.service.animation_inputs("run", "tenant", publish=True, sync_ref=self.ref)
        self.assertIs(value, self.bundle)
        inputs.assert_called_once_with("run", "tenant", publish=True, sync_ref=self.ref)
        self.assertIsNone(_ANIMATION_INPUT_CAPTURE.get())

    def test_scene_builder_calls_one_verified_composition_not_reconstruction(self):
        path = Path(__file__).resolve().parents[3] / "bie/productization/scene_ir_plan.py"
        module = ast.parse(path.read_text(encoding="utf-8"))
        function = next(node for node in module.body if isinstance(node, ast.FunctionDef) and node.name == "build_current_scene")
        calls = [node.func.attr for node in ast.walk(function) if isinstance(node, ast.Call)
                 and isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name)
                 and node.func.value.id == "service"]
        self.assertEqual(calls.count("verified_animation_with_inputs"), 1)
        self.assertNotIn("animation_inputs", calls)
        self.assertNotIn("verified_animation", calls)


if __name__ == "__main__": unittest.main()
