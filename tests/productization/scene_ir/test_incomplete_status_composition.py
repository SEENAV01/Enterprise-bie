"""Closed-scope controls plus actual persisted native upstream verification.

Pure mocks below demonstrate dispatch/noninterference, not artifact authority.
RealNativeIncompleteStatus separately exercises real stores and native admission.
"""
from contextlib import contextmanager, closing
from copy import deepcopy
from dataclasses import replace
import json
import secrets
from types import SimpleNamespace
import sqlite3
import unittest
from unittest.mock import patch

from bie.productization.contracts import ProducerError
from bie.productization.animation_slice import AnimationProducerService
from bie.productization.director_slice import DirectorProducerService
from bie.productization.pedagogy_slice import PedagogyProducerService
from bie.productization.scene_ir_slice import (SceneIRProducerService, STAGES,
    _INCOMPLETE_STATUS_CAPTURE, _ANIMATION_INPUT_CAPTURE,
    _DIRECTOR_STATUS_CAPTURE, _MOTION_INPUT_COMPOSITION)
from bie.director.director_revisions import RevisionError
from apps.operator.contracts import OperatorError
from .test_scene_ir_producer import PreparedSceneFixture
from .test_status_composition import DIRECTOR, VISUAL, ANIMATION


class IncompleteStatusScopeControls(unittest.TestCase):
    def setUp(self):
        self.service = object.__new__(SceneIRProducerService)
        self.output = SimpleNamespace(to_ref=lambda: 'exact-director-reference')
        self.director = dict.fromkeys(DIRECTOR, 'director')
        self.visual = dict.fromkeys(VISUAL, 'visual')
        self.animation = dict.fromkeys(ANIMATION, 'animation')
        for stage, receipt in (('DIRECTOR', self.director), ('VISUAL', self.visual), ('ANIMATION', self.animation)):
            receipt.update(attempt=1, output_artifact_id=stage, output_sha256=stage+'-sha',
                requires_review=True, accepted=False, release_ready=False, private='PRIVATE-DO-NOT-EXPORT')
        self.director.update(live_provider_executed=None, configured_provider_invoked=False)
        self.bundle = dict(director=self.output, visual_receipt=self.visual)
        self.plan = object()
        self.events = []
        self.states = dict.fromkeys(STAGES, 'SUCCEEDED'); self.states['SCENE_IR'] = 'READY'
        self.saved = dict(stages={s: dict(attempts=[dict(state=v, attempt=1,
            input_artifact_refs=[], output_artifact_refs=[s], evidence_refs=[s+'-evidence'])])
            for s, v in self.states.items()})
        self.service.persistence = SimpleNamespace(load_run_state=lambda *_: deepcopy(self.saved))
        self.base = dict(stages=deepcopy(self.states), product_accepted=False, opaque_lower_field='preserved')
        self.error = RuntimeError('synthetic private failure')

    def native_animation(self, service, run, tenant):
        self.events.append('animation')
        self.assertIs(service.verified_director(run, tenant)[0], self.output)
        _ANIMATION_INPUT_CAPTURE.get()['bundles'].append(self.bundle)
        return self.plan, self.animation

    def native_director(self, *_):
        self.events.append('director')
        return self.output, self.director

    @contextmanager
    def delegates(self, animation=None, director=None):
        with patch.object(AnimationProducerService, 'verified_animation', autospec=True,
                side_effect=animation or self.native_animation) as ani, \
             patch.object(DirectorProducerService, 'verified_director', autospec=True,
                side_effect=director or self.native_director) as direct:
            yield ani, direct

    def execute(self, animation=None, director=None):
        with self.delegates(animation, director):
            return self.service._incomplete_status_bundle('run', 'tenant')

    def clean(self):
        for scope in (_INCOMPLETE_STATUS_CAPTURE, _ANIMATION_INPUT_CAPTURE,
                _DIRECTOR_STATUS_CAPTURE, _MOTION_INPUT_COMPOSITION):
            self.assertIsNone(scope.get())
        self.assertEqual(set(vars(self.service)), {'persistence'})

    def status(self, *, lower=None, animation=None, director=None):
        with self.delegates(animation, director), \
             patch.object(PedagogyProducerService, 'status', autospec=True,
                side_effect=lower or (lambda *_: deepcopy(self.base))) as lower_call, \
             patch.object(AnimationProducerService, 'status', side_effect=AssertionError('DUPLICATE')), \
             patch.object(self.service, '_completed_status_bundle', side_effect=AssertionError('PREMATURE')), \
             patch.object(self.service, 'stage_ref', side_effect=lambda run, stage:
                (stage, SimpleNamespace(blob_digest=stage+'-sha'))):
            result = self.service.status('run', 'tenant')
            lower_call.assert_called_once_with(self.service, 'run', 'tenant')
            return result

    def test_one_fresh_native_proof_and_exact_director_return(self):
        proof, receipt = self.execute()
        self.assertIs(proof[0], self.plan); self.assertIs(proof[1], self.animation)
        self.assertIs(proof[2], self.bundle); self.assertIs(receipt, self.director)
        self.assertEqual(self.events, ['animation', 'director']); self.clean()

    def test_successive_operations_reopen_not_cache(self):
        self.execute(); self.clean(); self.execute(); self.clean()
        self.assertEqual(self.events, ['animation', 'director']*2)

    def test_missing_director_call_rejects(self):
        def action(*_):
            _ANIMATION_INPUT_CAPTURE.get()['bundles'].append(self.bundle)
            return self.plan, self.animation
        with self.assertRaises(ProducerError): self.execute(animation=action)
        self.clean()

    def test_missing_input_bundle_rejects(self):
        with self.assertRaises(ProducerError): self.execute(animation=lambda *_: (self.plan, self.animation))
        self.clean()

    def test_extra_input_bundle_rejects(self):
        def action(*args):
            result = self.native_animation(*args)
            _ANIMATION_INPUT_CAPTURE.get()['bundles'].append(self.bundle)
            return result
        with self.assertRaises(ProducerError): self.execute(animation=action)
        self.clean()

    def test_duplicate_director_rejects_before_second_native(self):
        def action(service, run, tenant):
            self.native_animation(service, run, tenant)
            service.verified_director(run, tenant)
        with self.assertRaises(ProducerError): self.execute(animation=action)
        self.assertEqual(self.events, ['animation', 'director']); self.clean()

    def test_caught_duplicate_poisoned(self):
        def action(*args):
            result = self.native_animation(*args)
            with self.assertRaises(ProducerError): args[0].verified_director(args[1], args[2])
            return result
        with self.assertRaises(ProducerError): self.execute(animation=action)
        self.clean()

    def test_foreign_run_rejects_before_native(self):
        with self.assertRaises(ProducerError):
            self.execute(animation=lambda service, run, tenant: service.verified_director('foreign', tenant))
        self.assertNotIn('director', self.events); self.clean()

    def test_foreign_tenant_rejects_before_native(self):
        with self.assertRaises(ProducerError):
            self.execute(animation=lambda service, run, tenant: service.verified_director(run, 'foreign'))
        self.assertNotIn('director', self.events); self.clean()

    def test_foreign_service_rejects_before_native(self):
        other = object.__new__(SceneIRProducerService)
        with self.assertRaises(ProducerError):
            self.execute(animation=lambda service, run, tenant: other.verified_director(run, tenant))
        self.assertNotIn('director', self.events); self.clean()

    def test_forged_animation_scope_rejects(self):
        def action(service, run, tenant):
            token = _ANIMATION_INPUT_CAPTURE.set(dict(service=service, run=run, tenant=tenant, bundles=[]))
            try: return service.verified_director(run, tenant)
            finally: _ANIMATION_INPUT_CAPTURE.reset(token)
        with self.assertRaises(ProducerError): self.execute(animation=action)
        self.clean()

    def test_missing_animation_scope_rejects(self):
        def action(service, run, tenant):
            token = _ANIMATION_INPUT_CAPTURE.set(None)
            try: return service.verified_director(run, tenant)
            finally: _ANIMATION_INPUT_CAPTURE.reset(token)
        with self.assertRaises(ProducerError): self.execute(animation=action)
        self.clean()

    def test_director_exception_identity_and_cleanup(self):
        with self.assertRaises(RuntimeError) as caught:
            self.execute(director=lambda *_: (_ for _ in ()).throw(self.error))
        self.assertIs(caught.exception, self.error); self.clean()

    def test_animation_exception_identity_and_cleanup(self):
        with self.assertRaises(RuntimeError) as caught:
            self.execute(animation=lambda *_: (_ for _ in ()).throw(self.error))
        self.assertIs(caught.exception, self.error); self.clean()

    def test_base_exception_identity_and_cleanup(self):
        error = KeyboardInterrupt()
        with self.assertRaises(KeyboardInterrupt) as caught:
            self.execute(director=lambda *_: (_ for _ in ()).throw(error))
        self.assertIs(caught.exception, error); self.clean()

    def test_caught_native_rejection_cannot_substitute_receipt(self):
        def action(service, run, tenant):
            with self.assertRaises(RuntimeError): service.verified_director(run, tenant)
            _ANIMATION_INPUT_CAPTURE.get()['bundles'].append(self.bundle)
            return self.plan, self.animation
        with self.assertRaises(ProducerError):
            self.execute(animation=action, director=lambda *_: (_ for _ in ()).throw(self.error))
        self.clean()

    def test_nested_operation_poisoned_even_when_caught(self):
        def action(*args):
            with self.assertRaises(ProducerError): self.service._incomplete_status_bundle('run', 'tenant')
            return self.native_animation(*args)
        with self.assertRaises(ProducerError): self.execute(animation=action)
        self.clean()

    def test_nested_status_poisoned(self):
        def action(*args):
            with self.assertRaises(ProducerError): self.service.status('run', 'tenant')
            return self.native_animation(*args)
        with self.assertRaises(ProducerError): self.execute(animation=action)
        self.clean()

    def test_reentrant_native_director_poisoned(self):
        def native(service, run, tenant):
            with self.assertRaises(ProducerError): service.verified_director(run, tenant)
            return self.output, self.director
        with self.assertRaises(ProducerError): self.execute(director=native)
        self.clean()

    def test_completed_capture_cannot_overlap(self):
        row = dict(invalid=False); token = _DIRECTOR_STATUS_CAPTURE.set(row)
        try:
            with self.assertRaises(ProducerError): self.execute()
            self.assertTrue(row['invalid']); self.assertIs(_DIRECTOR_STATUS_CAPTURE.get(), row)
        finally: _DIRECTOR_STATUS_CAPTURE.reset(token)
        self.clean()

    def test_motion_capture_cannot_overlap(self):
        row = dict(invalid=False); token = _MOTION_INPUT_COMPOSITION.set(row)
        try:
            with self.assertRaises(ProducerError): self.execute()
            self.assertTrue(row['invalid']); self.assertIs(_MOTION_INPUT_COMPOSITION.get(), row)
        finally: _MOTION_INPUT_COMPOSITION.reset(token)
        self.clean()

    def test_completed_admission_inside_new_scope_rejects(self):
        def action(*_): return self.service._completed_status_bundle('run', 'tenant')
        with self.assertRaises(ProducerError): self.execute(animation=action)
        self.clean()

    def test_motion_admission_inside_new_scope_rejects(self):
        def action(*_):
            with self.service.current_scene_motion_admission('run', 'tenant', lambda *_: None): pass
        with self.assertRaises(ProducerError): self.execute(animation=action)
        self.clean()

    def test_nested_animation_proof_rejects(self):
        def action(service, run, tenant): return service.verified_animation_with_inputs(run, tenant)
        with self.assertRaises(ProducerError): self.execute(animation=action)
        self.clean()

    def test_bundle_director_identity_mismatch_rejects(self):
        self.bundle['director'] = SimpleNamespace(to_ref=lambda: 'foreign')
        with self.assertRaises(ProducerError): self.execute()
        self.clean()

    def test_status_exact_allowlists_and_lower_result_conserved(self):
        result = self.status()
        self.assertEqual(result['director'], dict({k: self.director[k] for k in DIRECTOR},
            validation='PASS', director_executed=True, visual_input_validator='NOT_AVAILABLE_FOR_NATIVE_ARTIFACT_PAIR'))
        self.assertEqual(result['visual'], {k: self.visual[k] for k in VISUAL})
        self.assertEqual(result['animation'], {k: self.animation[k] for k in ANIMATION})
        self.assertEqual(result['opaque_lower_field'], 'preserved'); self.assertIsNone(result['scene_ir'])
        self.assertFalse(result['product_accepted']); self.assertIsNone(result['live_provider_executed'])
        self.assertFalse(result['configured_provider_invoked'])
        self.assertNotIn('PRIVATE-DO-NOT-EXPORT', repr(result)); self.clean()

    def test_lower_authority_error_before_native(self):
        with self.assertRaises(RuntimeError) as caught:
            self.status(lower=lambda *_: (_ for _ in ()).throw(self.error))
        self.assertIs(caught.exception, self.error); self.assertEqual(self.events, []); self.clean()

    def test_stage_change_between_selection_and_lower_status_rejects(self):
        self.base['stages']['ANIMATION'] = 'FAILED'
        with self.assertRaises(ProducerError): self.status()
        self.assertEqual(self.events, []); self.clean()

    def test_attempt_change_during_proof_rejects(self):
        def action(*args):
            result = self.native_animation(*args)
            self.saved['stages']['VISUAL']['attempts'][-1]['attempt'] = 2
            return result
        with self.assertRaises(ProducerError): self.status(animation=action)
        self.clean()

    def test_extra_evidence_during_proof_rejects(self):
        def action(*args):
            result = self.native_animation(*args)
            self.saved['stages']['ANIMATION']['attempts'][-1]['evidence_refs'].append('foreign')
            return result
        with self.assertRaises(ProducerError): self.status(animation=action)
        self.clean()

    def test_scene_completion_race_rejects_not_partial_projection(self):
        def action(*args):
            result = self.native_animation(*args)
            self.saved['stages']['SCENE_IR']['attempts'][-1]['state'] = 'SUCCEEDED'
            return result
        with self.assertRaises(ProducerError): self.status(animation=action)
        self.clean()

    def test_final_reconciliation_uses_one_whole_run_snapshot(self):
        original = self.service.persistence.load_run_state
        with patch.object(self.service.persistence, 'load_run_state', side_effect=original) as reads:
            self.status()
        # Selection, post-proof, final reconciliation: three complete snapshots,
        # not selection + post-proof + four independently sampled stage rows.
        self.assertEqual(reads.call_count, 3)

    def test_late_change_to_already_read_stage_rejects(self):
        original = self.service.persistence.load_run_state
        reads = 0
        def snapshot(run):
            nonlocal reads
            reads += 1
            if reads == 3:
                # Occurs after post-proof/output reconciliation and immediately
                # before the one required final whole-run snapshot is obtained.
                self.saved['stages']['VISUAL']['attempts'][-1]['attempt'] = 2
            return original(run)
        with patch.object(self.service.persistence, 'load_run_state', side_effect=snapshot):
            with self.assertRaises(ProducerError): self.status()
        self.clean()

    def test_output_identity_mismatch_rejects(self):
        self.animation['output_artifact_id'] = 'foreign'
        with self.assertRaises(ProducerError): self.status()

    def test_output_digest_mismatch_rejects(self):
        self.visual['output_sha256'] = 'foreign'
        with self.assertRaises(ProducerError): self.status()

    def test_receipt_attempt_mismatch_rejects(self):
        self.director['attempt'] = 2
        with self.assertRaises(ProducerError): self.status()

    def test_missing_public_field_fails_closed(self):
        del self.visual['plan_fingerprint']
        with self.assertRaises(KeyError): self.status()
        self.clean()

    def test_outside_scope_native_dispatch_unchanged(self):
        with patch.object(DirectorProducerService, 'verified_director', return_value=(self.output, self.director)) as native:
            result = self.service.verified_director('run', 'tenant')
            self.assertIs(result[0], self.output); native.assert_called_once_with('run', 'tenant')
        self.clean()

    def test_failure_then_success_restores_all_bindings(self):
        with self.assertRaises(RuntimeError): self.execute(animation=lambda *_: (_ for _ in ()).throw(self.error))
        self.clean(); self.execute(); self.clean()


class RealNativeIncompleteStatus(PreparedSceneFixture):
    def test_actual_projection_equals_full_legacy_without_scene_publication(self):
        with self.port.native(self.p, self.run, 'read') as service:
            before = deepcopy(service.persistence.load_run_state(self.run))
            expected = AnimationProducerService.status(service, self.run, self.p.tenant)
            expected['scene_ir'] = None
            native = DirectorProducerService.verified_director
            calls = []
            def actual(owner, run, tenant):
                calls.append((run, tenant)); return native(owner, run, tenant)
            with patch.object(DirectorProducerService, 'verified_director', autospec=True, side_effect=actual):
                result = service.status(self.run, self.p.tenant)
            self.assertEqual(result, expected)
            self.assertEqual(calls, [(self.run, self.p.tenant)])
            self.assertEqual(service.persistence.load_run_state(self.run), before)
            self.assertIsNone(result['scene_ir'])
            self.assertIsNone(_INCOMPLETE_STATUS_CAPTURE.get())

    def test_actual_successive_reads_are_fresh(self):
        with self.port.native(self.p, self.run, 'read') as service:
            original = AnimationProducerService.verified_animation
            with patch.object(AnimationProducerService, 'verified_animation', autospec=True, side_effect=original) as native:
                first = service.status(self.run, self.p.tenant)
                second = service.status(self.run, self.p.tenant)
            self.assertEqual(first, second); self.assertEqual(native.call_count, 2)

    def test_actual_stale_director_rejects_with_unchanged_cas_bytes(self):
        with self.port.native(self.p, self.run, 'read') as service:
            aid, record = service.stage_ref(self.run, 'DIRECTOR')
            state = deepcopy(service.persistence.load_run_state(self.run))
            with closing(sqlite3.connect(service.root/'director-state.sqlite3')) as db:
                with db: db.execute("UPDATE director_revisions SET state='STALE' WHERE run_id=?", (self.run,))
            with self.assertRaises(RevisionError): service.status(self.run, self.p.tenant)
            self.assertEqual(service.record(self.run, aid).blob_digest, record.blob_digest)
            self.assertEqual(service.persistence.load_run_state(self.run), state)

    def test_actual_private_parent_tamper_rejects(self):
        with self.port.native(self.p, self.run, 'read') as service:
            _, receipt = service.verified_animation(self.run, self.p.tenant)
            record = service.record(self.run, receipt['current_inputs_id'])
            from dataclasses import replace
            original = service.record
            def forged(run, aid):
                row = original(run, aid)
                return replace(row, parent_artifact_ids=row.parent_artifact_ids+['foreign-parent']) if aid==record.artifact_id else row
            with patch.object(service, 'record', side_effect=forged):
                with self.assertRaises(ProducerError): service.status(self.run, self.p.tenant)
            self.assertIsNone(_INCOMPLETE_STATUS_CAPTURE.get())

    def test_actual_revoked_authority_rejects(self):
        self.credentials._grants.clear()
        with self.assertRaises(OperatorError) as caught: self.port.status(self.p, self.run)
        self.assertEqual((caught.exception.code, caught.exception.status), ('unauthorized', 401))
        self.assertIsNone(_INCOMPLETE_STATUS_CAPTURE.get())

    def test_actual_cross_tenant_rejects(self):
        foreign = replace(self.p, actor='other-reader', tenant='foreign')
        self.credentials.grant(secrets.token_urlsafe(40), foreign)
        with self.assertRaises(ProducerError) as caught: self.port.status(foreign, self.run)
        self.assertEqual(caught.exception.code, 'foreign_run')
        self.assertIsNone(_INCOMPLETE_STATUS_CAPTURE.get())

    def test_actual_foreign_private_record_rejects(self):
        with self.port.native(self.p, self.run, 'read') as service:
            _, receipt = service.verified_animation(self.run, self.p.tenant)
            with closing(sqlite3.connect(service.persistence.path)) as db:
                with db: db.execute("UPDATE artifact_records SET run_id='foreign' WHERE artifact_id=?",
                    (receipt['current_inputs_id'],))
            with self.assertRaises(ProducerError): service.status(self.run, self.p.tenant)
        self.assertIsNone(_INCOMPLETE_STATUS_CAPTURE.get())

    def test_actual_extra_private_parent_rejects(self):
        with self.port.native(self.p, self.run, 'read') as service:
            _, receipt = service.verified_animation(self.run, self.p.tenant)
            source, _ = service.stage_ref(self.run, 'SOURCE')
            with closing(sqlite3.connect(service.persistence.path)) as db:
                with db: db.execute('INSERT INTO artifact_parents(artifact_id,parent_artifact_id) VALUES(?,?)',
                    (receipt['current_inputs_id'], source))
            with self.assertRaises(ProducerError): service.status(self.run, self.p.tenant)
        self.assertIsNone(_INCOMPLETE_STATUS_CAPTURE.get())

    def test_actual_future_fencing_receipt_rejects(self):
        with self.port.native(self.p, self.run, 'worker') as service:
            _, receipt = service.verified_animation(self.run, self.p.tenant)
            forged = dict(receipt, fencing_epoch=1000000)
            attempt = service.persistence.load_run_state(self.run)['stages']['ANIMATION']['attempts'][-1]
            old = service.record(self.run, attempt['evidence_refs'][0])
            aid = service.put(self.run, 'ANIMATION', 'producer.evidence', forged, old.parent_artifact_ids, True)
            with closing(sqlite3.connect(service.persistence.path)) as db:
                with db: db.execute("UPDATE attempts SET evidence_refs_json=? WHERE run_id=? AND stage_id='ANIMATION' AND attempt=?",
                    (json.dumps([aid]), self.run, attempt['attempt']))
            with self.assertRaises(ProducerError): service.status(self.run, self.p.tenant)
        self.assertIsNone(_INCOMPLETE_STATUS_CAPTURE.get())


if __name__ == '__main__': unittest.main()
