"""Pure phase controls plus actual current-artifact native entry/exit proof.

Inert tests establish adapter control flow, not native execution success. The
separate real-store cases and unchanged eleven-stage smoke remain mandatory.
"""
from contextlib import contextmanager, closing
from copy import deepcopy
import sqlite3
import unittest
from unittest.mock import patch

from bie.compiler import producer_motion_admission as admission
from bie.compiler.governed_motion import _ACTIVE
from bie.productization.animation_slice import AnimationProducerService
from bie.productization.contracts import ProducerError
from bie.productization.scene_ir_slice import (
    SceneIRProducerService, _ANIMATION_INPUT_CAPTURE, _MOTION_INPUT_COMPOSITION)
from bie.productization.scene_ir_contract import INPUT_COMPOSITION_POLICY, scene_ir_config
from bie.productization.scene_ir_plan import build_current_scene
from bie.director.director_revisions import RevisionError
from .test_scene_ir_producer import PreparedSceneFixture


class MotionCompositionControls(unittest.TestCase):
    def setUp(self):
        self.service = object.__new__(SceneIRProducerService)
        self.plan, self.receipt, self.bundle = {}, {}, {}
        self.element = {'element_id': 'synthetic-target'}
        self.prepared = {'derived': True}
        self.events, self.returned, self.catalogs = [], [], []
        self.error = RuntimeError('synthetic rejection; never exported')

    def native(self, service, run, tenant):
        phase = _MOTION_INPUT_COMPOSITION.get()['phase']
        self.events.append('native:' + phase)
        service.animation_inputs(run, tenant, sync_ref=object())
        self.returned.append((self.plan, self.receipt))
        return self.plan, self.receipt

    def derive(self, plan, receipt, bundle):
        self.events.append('derive')
        self.assertIs(plan, self.plan)
        self.assertIs(receipt, self.receipt)
        self.assertIs(bundle, self.bundle)
        return self.prepared, [self.element]

    def snapshot(self, service, run, tenant):
        phase = _MOTION_INPUT_COMPOSITION.get()['phase']
        plan, receipt = service.verified_animation(run, tenant)
        self.assertIs(plan, self.plan)
        self.assertIs(receipt, self.receipt)
        self.events.append('snapshot:' + phase)
        return {'plan': deepcopy(plan), 'receipt': deepcopy(receipt)}

    def lower(self, snapshot, elements, presentation):
        self.events.append('lower')
        self.catalogs.append(elements)
        self.assertEqual(elements, [self.element])
        self.assertIs(elements, _MOTION_INPUT_COMPOSITION.get()['catalog'])
        return {'identity': 'synthetic', 'tracks': {}}

    @contextmanager
    def runtime(self, *, native=None, derive=None, snapshot=None):
        with patch.object(AnimationProducerService, 'verified_animation', autospec=True,
                side_effect=native or self.native) as verified, \
             patch.object(AnimationProducerService, 'animation_inputs', return_value=self.bundle), \
             patch.object(admission, '_snapshot', side_effect=snapshot or self.snapshot), \
             patch.object(admission, '_lower', side_effect=self.lower):
            with self.service.current_scene_motion_admission('run', 'tenant', derive or self.derive) as value:
                yield value, verified

    def clean(self):
        self.assertIsNone(_ANIMATION_INPUT_CAPTURE.get())
        self.assertIsNone(_MOTION_INPUT_COMPOSITION.get())
        self.assertIsNone(_ACTIVE.get())
        self.assertEqual(vars(self.service), {})

    def test_two_fresh_native_calls_no_preparatory_third_call(self):
        with self.runtime() as ((bound, prepared), verified):
            self.assertIs(prepared, self.prepared)
            self.assertEqual(verified.call_count, 1)
            self.events.append('body')
        self.assertEqual(verified.call_count, 2)
        self.assertEqual(self.events, ['native:ENTRY', 'derive', 'snapshot:ENTRY', 'lower',
            'body', 'native:EXIT', 'snapshot:EXIT'])
        self.clean()

    def test_full_native_delegation_arguments_unchanged(self):
        with self.runtime() as (_, verified):
            pass
        self.assertEqual(verified.call_args_list, [unittest.mock.call(self.service, 'run', 'tenant')] * 2)

    def test_original_plan_and_receipt_return_identity(self):
        with self.runtime():
            pass
        self.assertEqual(len(self.returned), 2)
        self.assertTrue(all(p is self.plan and r is self.receipt for p, r in self.returned))

    def test_catalog_factory_once_before_canonical_lower(self):
        with self.runtime():
            self.assertEqual(self.events.count('derive'), 1)
        self.assertEqual(self.events.count('derive'), 1)
        self.assertLess(self.events.index('derive'), self.events.index('lower'))

    def test_body_cannot_consume_exit_call(self):
        with self.assertRaisesRegex(ProducerError, 'scene_ir_motion_composition_scope'):
            with self.runtime() as (_, native):
                self.service.verified_animation('run', 'tenant')
        self.assertEqual(native.call_count, 1)
        self.clean()

    def test_caught_body_violation_still_poisoned(self):
        with self.assertRaisesRegex(ProducerError, 'scene_ir_motion_composition_scope'):
            with self.runtime() as (_, native):
                with self.assertRaises(ProducerError):
                    self.service.verified_animation('run', 'tenant')
        self.assertEqual(native.call_count, 1)
        self.clean()

    def test_foreign_run_rejected_before_native(self):
        with self.assertRaises(ProducerError):
            with self.runtime() as (_, native):
                self.service.verified_animation('foreign', 'tenant')
        self.assertEqual(native.call_count, 1)

    def test_foreign_tenant_rejected_before_native(self):
        with self.assertRaises(ProducerError):
            with self.runtime() as (_, native):
                self.service.verified_animation('run', 'foreign')
        self.assertEqual(native.call_count, 1)

    def test_foreign_service_rejected_before_native(self):
        foreign = object.__new__(SceneIRProducerService)
        with self.assertRaises(ProducerError):
            with self.runtime() as (_, native):
                foreign.verified_animation('run', 'tenant')
        self.assertEqual(native.call_count, 1)

    def test_nested_composition_rejected(self):
        with self.assertRaisesRegex(ProducerError, 'scene_ir_motion_composition_scope'):
            with self.runtime():
                with self.assertRaisesRegex(ProducerError, 'scene_ir_motion_composition_nested'):
                    with self.service.current_scene_motion_admission('run', 'tenant', self.derive):
                        self.fail('nested scope admitted')
        self.clean()

    def test_nested_existing_input_capture_rejected_without_replacing_it(self):
        sentinel = {}
        marker = _ANIMATION_INPUT_CAPTURE.set(sentinel)
        try:
            with self.assertRaises(ProducerError):
                with self.service.current_scene_motion_admission('run', 'tenant', self.derive):
                    self.fail('nested capture admitted')
            self.assertIs(_ANIMATION_INPUT_CAPTURE.get(), sentinel)
            self.assertIsNone(_MOTION_INPUT_COMPOSITION.get())
        finally:
            _ANIMATION_INPUT_CAPTURE.reset(marker)

    def test_entry_native_failure_identity_and_restoration(self):
        with self.assertRaises(RuntimeError) as caught:
            with self.runtime(native=lambda *_: (_ for _ in ()).throw(self.error)):
                self.fail('failed entry yielded')
        self.assertIs(caught.exception, self.error)
        self.clean()

    def test_factory_failure_identity_and_no_exit_or_retry(self):
        with self.assertRaises(RuntimeError) as caught:
            with self.runtime(derive=lambda *_: (_ for _ in ()).throw(self.error)):
                self.fail('failed derivation yielded')
        self.assertIs(caught.exception, self.error)
        self.assertEqual(self.events, ['native:ENTRY'])
        self.clean()

    def test_exit_native_failure_identity_and_restoration(self):
        def native(service, run, tenant):
            if _MOTION_INPUT_COMPOSITION.get()['phase'] == 'EXIT':
                raise self.error
            return self.native(service, run, tenant)
        with self.assertRaises(RuntimeError) as caught:
            with self.runtime(native=native):
                pass
        self.assertIs(caught.exception, self.error)
        self.clean()

    def test_body_failure_identity_and_original_no_exit_behavior(self):
        with self.assertRaises(RuntimeError) as caught:
            with self.runtime() as (_, native):
                raise self.error
        self.assertIs(caught.exception, self.error)
        self.assertEqual(native.call_count, 1)
        self.clean()

    def test_attempt_count_precedes_native_call(self):
        def native(service, run, tenant):
            capture = _MOTION_INPUT_COMPOSITION.get()
            self.assertEqual(capture['attempts'], 1 if capture['phase'] == 'ENTRY' else 2)
            return self.native(service, run, tenant)
        with self.runtime(native=native):
            pass

    def test_native_failure_cannot_retry_inside_entry_scope(self):
        def snapshot(service, run, tenant):
            for _ in range(2):
                try:
                    service.verified_animation(run, tenant)
                except RuntimeError:
                    continue
            self.fail('retry admitted')
        with self.assertRaisesRegex(ProducerError, 'scene_ir_motion_composition_scope'):
            with self.runtime(native=lambda *_: (_ for _ in ()).throw(self.error), snapshot=snapshot):
                pass
        self.clean()

    def test_exit_snapshot_equality_remains_mandatory(self):
        with self.assertRaisesRegex(ValueError, 'CURRENTNESS_CHANGED'):
            with self.runtime():
                self.plan['changed'] = True
        self.clean()

    def test_fresh_exit_can_reject_unchanged_artifact_payload(self):
        def native(service, run, tenant):
            if _MOTION_INPUT_COMPOSITION.get()['phase'] == 'EXIT':
                raise self.error
            return self.native(service, run, tenant)
        original = deepcopy(self.plan)
        with self.assertRaises(RuntimeError):
            with self.runtime(native=native):
                self.assertEqual(self.plan, original)
        self.assertEqual(self.plan, original)

    def test_separate_operations_have_distinct_owned_catalogs(self):
        for _ in range(2):
            with self.runtime():
                pass
        self.assertEqual(len(self.catalogs), 2)
        self.assertIsNot(self.catalogs[0], self.catalogs[1])
        self.assertEqual(self.events.count('native:ENTRY'), 2)
        self.assertEqual(self.events.count('native:EXIT'), 2)
        self.clean()

    def test_no_factory_or_proof_retained_on_service(self):
        with self.runtime():
            pass
        self.clean()

    def test_no_native_recursion_through_override(self):
        with self.runtime() as (_, native):
            pass
        self.assertEqual(native.call_count, 2)

    def test_empty_catalog_rejected_before_lower(self):
        with self.assertRaisesRegex(ProducerError, 'scene_ir_motion_composition_catalog'):
            with self.runtime(derive=lambda *_: ({}, [])):
                pass
        self.assertNotIn('lower', self.events)

    def test_non_list_catalog_rejected(self):
        with self.assertRaises(ProducerError):
            with self.runtime(derive=lambda *_: ({}, (self.element,))):
                pass

    def test_non_dict_prepared_rejected(self):
        with self.assertRaises(ProducerError):
            with self.runtime(derive=lambda *_: ([], [self.element])):
                pass

    def test_missing_entry_not_false_success(self):
        with patch.object(self, 'lower', return_value={'identity': 'synthetic'}):
            with self.assertRaisesRegex(ProducerError, 'scene_ir_motion_composition_entry'):
                with self.runtime(snapshot=lambda *_: {}):
                    pass
        self.clean()

    def test_non_callable_factory_rejected_without_scope(self):
        with self.assertRaises(ProducerError):
            with self.service.current_scene_motion_admission('run', 'tenant', None):
                pass
        self.clean()

    def test_outside_scope_original_native_dispatch(self):
        value = (self.plan, self.receipt)
        with patch.object(AnimationProducerService, 'verified_animation', return_value=value) as native:
            self.assertIs(self.service.verified_animation('run', 'tenant'), value)
        native.assert_called_once_with('run', 'tenant')
        self.clean()

    def test_explicit_versioned_policy_in_configuration(self):
        self.assertEqual(scene_ir_config()['input_composition_policy'], INPUT_COMPOSITION_POLICY)
        self.assertEqual(INPUT_COMPOSITION_POLICY, 'fresh-m1-entry-catalog-and-fresh-exit/1')

    def test_direct_capture_cannot_bypass_body_counter(self):
        with self.assertRaisesRegex(ProducerError, 'scene_ir_motion_composition_scope'):
            with self.runtime() as (_, native):
                with self.assertRaises(ProducerError):
                    self.service.verified_animation_with_inputs('run', 'tenant')
        self.assertEqual(native.call_count, 1)
        self.clean()

    def test_factory_cannot_start_extra_direct_capture(self):
        def derive(*_):
            with self.assertRaises(ProducerError):
                self.service.verified_animation_with_inputs('run', 'tenant')
            return self.prepared, [self.element]
        with self.assertRaises(ProducerError):
            with self.runtime(derive=derive):
                self.fail('invalid entry yielded')
        self.clean()

    def test_delegation_flag_restored_before_derivation(self):
        def derive(*args):
            self.assertFalse(_MOTION_INPUT_COMPOSITION.get()['delegating'])
            return self.derive(*args)
        with self.runtime(derive=derive):
            self.assertFalse(_MOTION_INPUT_COMPOSITION.get()['delegating'])
        self.clean()

    def test_fresh_operation_after_failure_reopens_authority(self):
        with self.assertRaises(RuntimeError):
            with self.runtime(native=lambda *_: (_ for _ in ()).throw(self.error)):
                pass
        with self.runtime() as (_, native):
            pass
        self.assertEqual(native.call_count, 2)
        self.clean()

    def test_caught_reentrant_capture_poisoned_before_third_native_call(self):
        def native(service, run, tenant):
            with self.assertRaises(ProducerError):
                service.verified_animation_with_inputs(run, tenant)
            return self.native(service, run, tenant)
        with self.assertRaises(ProducerError):
            with self.runtime(native=native):
                self.fail('reentrant native capture admitted')
        self.assertNotIn('native:EXIT', self.events)
        self.clean()


class RealNativeAdmissionComposition(PreparedSceneFixture):
    def test_actual_upstream_artifacts_execute_two_fresh_native_proofs(self):
        original = AnimationProducerService.verified_animation
        phases = []
        def native(service, run, tenant):
            phases.append(_MOTION_INPUT_COMPOSITION.get()['phase'])
            return original(service, run, tenant)
        with self.port.native(self.p, self.run, 'read') as service:
            with patch.object(AnimationProducerService, 'verified_animation', autospec=True, side_effect=native):
                document, private, bundle, receipt = build_current_scene(service, self.run, self.p.tenant)
            self.assertEqual(phases, ['ENTRY', 'EXIT'])
            self.assertEqual(private['input_composition_policy'], INPUT_COMPOSITION_POLICY)
            self.assertEqual(private['native_gate']['passed'], True)
            self.assertFalse(document.accepted)
            self.assertEqual(receipt['output_artifact_id'], service.stage_ref(self.run, 'ANIMATION')[0])
        self.assertIsNone(_MOTION_INPUT_COMPOSITION.get())
        self.assertIsNone(_ANIMATION_INPUT_CAPTURE.get())

    def test_actual_native_revision_invalidation_rejects_exit_without_byte_change(self):
        original = AnimationProducerService.verified_animation
        phases = []
        def native(service, run, tenant):
            phases.append(_MOTION_INPUT_COMPOSITION.get()['phase'])
            return original(service, run, tenant)
        with self.port.native(self.p, self.run, 'read') as service:
            ref, row = service.stage_ref(self.run, 'DIRECTOR')
            original_digest = row.blob_digest
            def invalidate(boundary):
                if boundary == 'after_SCENE_IR_validation':
                    with closing(sqlite3.connect(service.root / 'director-state.sqlite3')) as db:
                        with db:
                            db.execute("UPDATE director_revisions SET state='STALE' WHERE run_id=?", (self.run,))
                        self.assertEqual(db.execute('SELECT state FROM director_revisions WHERE run_id=?',
                            (self.run,)).fetchone(), ('STALE',))
            with patch.object(AnimationProducerService, 'verified_animation', autospec=True, side_effect=native):
                with self.assertRaises(RevisionError):
                    build_current_scene(service, self.run, self.p.tenant, fault=invalidate)
            self.assertEqual(phases, ['ENTRY', 'EXIT'])
            self.assertEqual(service.record(self.run, ref).blob_digest, original_digest)
            self.assertEqual(service.persistence.load_run_state(self.run)['stages']['SCENE_IR']['attempts'][-1]['state'], 'PENDING')
        self.assertIsNone(_MOTION_INPUT_COMPOSITION.get())
        self.assertIsNone(_ANIMATION_INPUT_CAPTURE.get())


if __name__ == '__main__':
    unittest.main()
