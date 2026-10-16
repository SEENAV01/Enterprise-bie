"""Fresh native EXIT projection: inert controls and separate real-store proof."""
from contextlib import contextmanager, closing
from copy import deepcopy
from types import SimpleNamespace
import sqlite3
import unittest
from unittest.mock import patch

from bie.productization.contracts import ProducerError
from bie.productization.director_slice import DirectorProducerService
from bie.productization.pedagogy_slice import PedagogyProducerService
from bie.productization.scene_ir_slice import (SceneIRProducerService,
    _DIRECTOR_STATUS_CAPTURE, _MOTION_INPUT_COMPOSITION, _ANIMATION_INPUT_CAPTURE)
from bie.director.director_revisions import RevisionError
from .test_status_composition import DIRECTOR, VISUAL, ANIMATION, SCENE
from .test_scene_ir_producer import PreparedSceneFixture


class DirectorStatusCaptureControls(unittest.TestCase):
    def setUp(self):
        self.service = object.__new__(SceneIRProducerService)
        self.ref = object()
        self.output = SimpleNamespace(to_ref=lambda: self.ref)
        self.receipt = dict.fromkeys(DIRECTOR, 'synthetic-director')
        self.receipt.update(live_provider_executed=False, configured_provider_invoked=True,
            requires_review=True, accepted=False, release_ready=False, private='must never escape')
        self.value = (self.output, self.receipt)
        self.bundle = ({}, {}, {'director': self.output}, {})
        self.events = []
        self.error = RuntimeError('synthetic private exception')

    @contextmanager
    def phase(self, name='EXIT', **changes):
        row = dict(service=self.service, run='run', tenant='tenant', phase=name,
            delegating=True, invalid=False)
        row.update(changes)
        token = _MOTION_INPUT_COMPOSITION.set(row)
        try: yield row
        finally: _MOTION_INPUT_COMPOSITION.reset(token)

    def native(self, service, run, tenant):
        self.events.append(_MOTION_INPUT_COMPOSITION.get()['phase'])
        return self.value

    def complete(self, *_):
        for phase in ('ENTRY', 'EXIT'):
            with self.phase(phase):
                value = self.service.verified_director('run', 'tenant')
                self.assertIs(value, self.value)
        return self.bundle

    def execute(self, action=None, native=None):
        with patch.object(DirectorProducerService, 'verified_director', autospec=True,
                side_effect=native or self.native) as delegated, \
             patch.object(self.service, '_verified_scene_bundle', side_effect=action or self.complete):
            value = self.service._completed_status_bundle('run', 'tenant')
        return value, delegated

    def clean(self):
        self.assertIsNone(_DIRECTOR_STATUS_CAPTURE.get())
        self.assertIsNone(_MOTION_INPUT_COMPOSITION.get())
        self.assertIsNone(_ANIMATION_INPUT_CAPTURE.get())
        self.assertEqual(vars(self.service), {})

    def test_exact_successful_exit_return_and_two_fresh_native_delegations(self):
        value, delegated = self.execute()
        self.assertIs(value[0], self.bundle)
        self.assertIs(value[1], self.receipt)
        self.assertEqual(self.events, ['ENTRY', 'EXIT'])
        self.assertEqual(delegated.call_args_list, [unittest.mock.call(self.service, 'run', 'tenant')]*2)
        self.clean()

    def test_entry_is_not_retained_as_exit(self):
        entry = self.output, {'old': True}
        def native(service, run, tenant):
            if _MOTION_INPUT_COMPOSITION.get()['phase']=='ENTRY': return entry
            return self.value
        def action(*_):
            with self.phase('ENTRY'):
                self.assertIs(self.service.verified_director('run','tenant'),entry)
            with self.phase():
                self.assertIs(self.service.verified_director('run','tenant'),self.value)
            return self.bundle
        result, _ = self.execute(action=action,native=native)
        self.assertIs(result[1], self.receipt)

    def test_each_operation_reopens_native_authority(self):
        self.execute()
        self.receipt = dict(self.receipt, output_sha256='changed')
        self.value = self.output, self.receipt
        value, native = self.execute()
        self.assertEqual(native.call_count, 2)
        self.assertIs(value[1], self.receipt)
        self.clean()

    def test_missing_both_native_calls_rejects(self):
        with self.assertRaises(ProducerError): self.execute(action=lambda *_: self.bundle)
        self.clean()

    def test_missing_exit_rejects(self):
        def action(*_):
            with self.phase('ENTRY'): self.service.verified_director('run','tenant')
            return self.bundle
        with self.assertRaises(ProducerError): self.execute(action=action)
        self.clean()

    def test_missing_entry_rejects(self):
        def action(*_):
            with self.phase(): self.service.verified_director('run','tenant')
            return self.bundle
        with self.assertRaises(ProducerError): self.execute(action=action)

    def test_duplicate_exit_is_poisoned_even_when_caught(self):
        def action(*_):
            self.complete()
            with self.phase():
                with self.assertRaises(ProducerError): self.service.verified_director('run','tenant')
            return self.bundle
        with self.assertRaises(ProducerError): self.execute(action=action)
        self.clean()

    def test_duplicate_entry_rejects_before_second_native_call(self):
        def action(*_):
            with self.phase('ENTRY'):
                self.service.verified_director('run','tenant')
                self.service.verified_director('run','tenant')
        with self.assertRaises(ProducerError): self.execute(action=action)
        self.assertEqual(self.events, ['ENTRY'])

    def test_foreign_run_rejects_before_native(self):
        def action(*_):
            with self.phase(): self.service.verified_director('foreign','tenant')
        with self.assertRaises(ProducerError): self.execute(action=action)
        self.assertEqual(self.events, [])

    def test_foreign_tenant_rejects_before_native(self):
        def action(*_):
            with self.phase(): self.service.verified_director('run','foreign')
        with self.assertRaises(ProducerError): self.execute(action=action)
        self.assertEqual(self.events, [])

    def test_foreign_service_rejects_before_native(self):
        other = object.__new__(SceneIRProducerService)
        def action(*_):
            with self.phase(): other.verified_director('run','tenant')
        with self.assertRaises(ProducerError): self.execute(action=action)
        self.assertEqual(self.events, [])

    def test_wrong_phase_rejects(self):
        def action(*_):
            with self.phase('BODY'): self.service.verified_director('run','tenant')
        with self.assertRaises(ProducerError): self.execute(action=action)

    def test_unscoped_native_call_rejects(self):
        with self.assertRaises(ProducerError):
            self.execute(action=lambda *_: self.service.verified_director('run','tenant'))

    def test_not_delegating_rejects(self):
        def action(*_):
            with self.phase(delegating=False): self.service.verified_director('run','tenant')
        with self.assertRaises(ProducerError): self.execute(action=action)

    def test_invalid_motion_scope_rejects(self):
        def action(*_):
            with self.phase(invalid=True): self.service.verified_director('run','tenant')
        with self.assertRaises(ProducerError): self.execute(action=action)

    def test_caught_nested_operation_poisoned(self):
        def action(*_):
            with self.assertRaises(ProducerError): self.service._completed_status_bundle('run','tenant')
            return self.complete()
        with self.assertRaises(ProducerError): self.execute(action=action)
        self.clean()

    def test_existing_motion_scope_rejects_without_retention(self):
        with self.phase() as row:
            with self.assertRaises(ProducerError): self.service._completed_status_bundle('run','tenant')
            self.assertTrue(row['invalid'])
        self.clean()

    def test_native_exit_exception_identity_and_cleanup(self):
        def native(service, run, tenant):
            if _MOTION_INPUT_COMPOSITION.get()['phase']=='EXIT': raise self.error
            return self.value
        with self.assertRaises(RuntimeError) as caught: self.execute(native=native)
        self.assertIs(caught.exception, self.error)
        self.clean()

    def test_native_entry_exception_identity_and_cleanup(self):
        with self.assertRaises(RuntimeError) as caught:
            self.execute(native=lambda *_: (_ for _ in ()).throw(self.error))
        self.assertIs(caught.exception,self.error)
        self.clean()

    def test_caught_native_entry_rejection_poisoned_before_exit(self):
        def action(*_):
            with self.phase('ENTRY'):
                with self.assertRaises(RuntimeError) as caught:
                    self.service.verified_director('run','tenant')
                self.assertIs(caught.exception,self.error)
            self.assertTrue(_DIRECTOR_STATUS_CAPTURE.get()['invalid'])
            with self.phase():
                with self.assertRaises(ProducerError): self.service.verified_director('run','tenant')
            return self.bundle
        with self.assertRaises(ProducerError):
            self.execute(action=action,native=lambda *_: (_ for _ in ()).throw(self.error))
        self.clean()

    def test_caught_native_exit_rejection_cannot_return_completed_bundle(self):
        def native(service,run,tenant):
            if _MOTION_INPUT_COMPOSITION.get()['phase']=='EXIT': raise self.error
            return self.value
        def action(*_):
            with self.phase('ENTRY'): self.service.verified_director('run','tenant')
            with self.phase():
                with self.assertRaises(RuntimeError) as caught:
                    self.service.verified_director('run','tenant')
                self.assertIs(caught.exception,self.error)
            return self.bundle
        with self.assertRaises(ProducerError): self.execute(action=action,native=native)
        self.clean()

    def test_later_full_scene_verification_rejection_is_not_bypassed(self):
        def action(*_):
            self.complete()
            raise self.error
        with self.assertRaises(RuntimeError) as caught: self.execute(action=action)
        self.assertIs(caught.exception,self.error)
        self.clean()

    def test_reentrant_exit_poisoned_even_when_native_catches(self):
        def native(service, run, tenant):
            if _MOTION_INPUT_COMPOSITION.get()['phase']=='EXIT':
                with self.assertRaises(ProducerError): service.verified_director(run,tenant)
            return self.value
        with self.assertRaises(ProducerError): self.execute(native=native)
        self.clean()

    def test_exit_target_identity_mismatch_rejects(self):
        self.bundle[2]['director'] = SimpleNamespace(to_ref=lambda: object())
        with self.assertRaises(ProducerError): self.execute()

    def test_no_cross_scope_retention_after_failure_then_success(self):
        with self.assertRaises(RuntimeError): self.execute(native=lambda *_: (_ for _ in ()).throw(self.error))
        self.clean()
        self.execute()
        self.clean()

    def test_native_dispatch_outside_status_scope_is_unchanged(self):
        with patch.object(DirectorProducerService,'verified_director',return_value=self.value) as native:
            self.assertIs(self.service.verified_director('run','tenant'),self.value)
            native.assert_called_once_with('run','tenant')

    def test_completed_branch_stage_map_change_fails_closed(self):
        self.service.persistence=SimpleNamespace(load_run_state=lambda *_: {'stages':{'SCENE_IR':{'attempts':[{'state':'SUCCEEDED'}]}}})
        with patch.object(PedagogyProducerService,'status',return_value={'stages':{'SCENE_IR':'READY'}}), \
             patch.object(self.service,'_completed_status_bundle') as verified:
            with self.assertRaises(ProducerError): self.service.status('run','tenant')
            verified.assert_not_called()


class RealNativeDirectorStatusComposition(PreparedSceneFixture):
    def completed(self, service):
        value=service.work_once(self.run,self.p.tenant)
        self.assertTrue(value['slice_complete'])
        self.assertEqual(value['stages']['SCENE_IR'],'SUCCEEDED')

    def test_actual_completed_status_equals_full_legacy_projection_with_two_fresh_proofs(self):
        original=DirectorProducerService.verified_director
        phases=[]
        def native(service,run,tenant):
            phases.append(_MOTION_INPUT_COMPOSITION.get()['phase'])
            return original(service,run,tenant)
        with self.port.native(self.p,self.run,'read') as service:
            self.completed(service)
            expected=DirectorProducerService.status(service,self.run,self.p.tenant)
            _,receipt,bundle,animation=service._verified_scene_bundle(self.run,self.p.tenant)
            expected['visual']={k:bundle['visual_receipt'][k] for k in VISUAL}
            expected['animation']={k:animation[k] for k in ANIMATION}
            expected['scene_ir']={k:receipt[k] for k in SCENE}
            with patch.object(DirectorProducerService,'verified_director',autospec=True,side_effect=native):
                actual=service.status(self.run,self.p.tenant)
            self.assertEqual(phases,['ENTRY','EXIT'])
            self.assertEqual(actual,expected)
        self.assertIsNone(_DIRECTOR_STATUS_CAPTURE.get())

    def test_actual_exit_stale_revision_rejects_status_with_unchanged_blob(self):
        original=DirectorProducerService.verified_director
        phases=[]
        with self.port.native(self.p,self.run,'read') as service:
            self.completed(service)
            ref,row=service.stage_ref(self.run,'DIRECTOR')
            before=deepcopy(service.persistence.load_run_state(self.run))
            def native(owner,run,tenant):
                phase=_MOTION_INPUT_COMPOSITION.get()['phase'];phases.append(phase)
                if phase=='EXIT':
                    with closing(sqlite3.connect(service.root/'director-state.sqlite3')) as db:
                        with db: db.execute("UPDATE director_revisions SET state='STALE' WHERE run_id=?",(self.run,))
                        self.assertEqual(db.execute('SELECT state FROM director_revisions WHERE run_id=?',
                            (self.run,)).fetchone(),('STALE',))
                return original(owner,run,tenant)
            with patch.object(DirectorProducerService,'verified_director',autospec=True,side_effect=native):
                with self.assertRaises(RevisionError): service.status(self.run,self.p.tenant)
            self.assertEqual(phases,['ENTRY','EXIT'])
            self.assertEqual(service.record(self.run,ref).blob_digest,row.blob_digest)
            self.assertEqual(service.persistence.load_run_state(self.run),before)
        self.assertIsNone(_DIRECTOR_STATUS_CAPTURE.get())
        self.assertIsNone(_MOTION_INPUT_COMPOSITION.get())


if __name__=='__main__': unittest.main()
