"""Negative conservation checks on reopened real source-derived native records.

The pure perturbations are not replacement catalogs or process evidence. Their
baseline is produced by the actual ten predecessors and current native adapter.
"""
from copy import deepcopy
from dataclasses import replace
import unittest

from .test_scene_ir_producer import SceneFixture, CHART
from bie.productization.scene_ir_plan import build_current_scene, validate_handoff, scene_scope, consumer_policy
from bie.productization.scene_ir_catalog import verify_inventory
from bie.productization.contracts import digest, ProducerError
from bie.productization.director_storage import native_runtime
from bie.director.director_consumers import DirectorConsumers
from bie.director.director_revisions import DirectorRevisionStore


class ConservationControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        f = SceneFixture()
        try:
            f.setUp(); f.admit((CHART,)); f.upstream()
            with f.port.native(f.p, f.run, 'read') as service:
                doc, private, bundle, receipt = build_current_scene(service, f.run, f.p.tenant)
                cls.rows = bundle['rows']
                cls.plan, _ = service.verified_animation(f.run, f.p.tenant)
                cls.handoff = service.read(f.run, receipt['handoff_id'])
                cls.catalog, cls.mappings = doc.to_dict()['elements'], private['catalog_mapping']
                cls.scope = private['scope']
                cls.target = service.configuration(f.run, f.p.tenant)['config']['visual']['target']
                cls.private = private
                with native_runtime(service, f.run, None) as native:
                    ref, _ = service.stage_ref(f.run, 'DIRECTOR')
                    _, cls.execution = DirectorConsumers(native.io, DirectorRevisionStore(native.idempotency))._director(
                        native.io.load(ref).to_ref())
        finally:
            if hasattr(f, 'tmp'): f.tearDown()

    def inventory_reject(self, change):
        rows, catalog, mappings = (deepcopy(self.rows), deepcopy(self.catalog), deepcopy(self.mappings))
        change(rows, catalog, mappings)
        # Even a recomputed producer-side props digest cannot bless source loss.
        for m in mappings:
            m['native_props_sha256'] = {e['element_id']: digest(e['props']) for e in catalog
                                       if e['element_id'] in m['native_element_ids']}
        with self.assertRaises(Exception):
            verify_inventory(rows, catalog, mappings, self.target)

    def node_reject(self, change):
        handoff = deepcopy(self.handoff)
        change(handoff)
        with self.assertRaises(Exception):
            validate_handoff(handoff, self.plan, self.rows, self.catalog, self.scope)

    def test_actual_catalog_independently_conserves_inventory(self):
        self.assertTrue(verify_inventory(self.rows, self.catalog, self.mappings, self.target)['passed'])

    def test_changed_values_with_recomputed_digest_rejected(self):
        self.inventory_reject(lambda r, c, m: next(e for e in c if e['element_type'] == 'chart')['props']['values'].__setitem__(0, 999))

    def test_changed_categories_rejected(self):
        self.inventory_reject(lambda r, c, m: next(e for e in c if e['element_type'] == 'chart')['props']['categories'].__setitem__(0, 'invented'))

    def test_changed_axis_label_rejected(self):
        self.inventory_reject(lambda r, c, m: next(e for e in c if e['element_type'] == 'chart')['props'].update(x_label='invented'))

    def test_invented_units_rejected(self):
        self.inventory_reject(lambda r, c, m: next(e for e in c if e['element_type'] == 'chart')['props'].update(units='invented'))

    def test_static_label_loss_rejected(self):
        self.inventory_reject(lambda r, c, m: c.remove(next(e for e in c if e['element_type'] == 'text')))

    def test_static_geometry_change_rejected(self):
        self.inventory_reject(lambda r, c, m: next(e for e in c if e['element_type'] == 'shape')['props']['geometry']['points'][0].__setitem__(0, 20))

    def test_static_text_changed_rejected(self):
        self.inventory_reject(lambda r, c, m: next(e for e in c if e['element_type'] == 'text')['props'].update(text='invented'))

    def test_foreign_evidence_rejected(self):
        self.inventory_reject(lambda r, c, m: c[0].update(source_refs=['foreign']))

    def test_foreign_reasoning_rejected(self):
        self.inventory_reject(lambda r, c, m: c[0].update(reasoning_refs=['foreign']))

    def test_layout_redesign_rejected(self):
        self.inventory_reject(lambda r, c, m: c[0]['normalized_box'].update(x=0))

    def test_duplicate_element_rejected(self):
        self.inventory_reject(lambda r, c, m: c.append(deepcopy(c[0])))

    def test_orphan_mapping_rejected(self):
        self.inventory_reject(lambda r, c, m: m[0].update(primitive_id='foreign'))

    def test_duplicate_mapping_rejected(self):
        self.inventory_reject(lambda r, c, m: m.append(deepcopy(m[0])))

    def test_stale_visual_revision_rejected(self):
        self.inventory_reject(lambda r, c, m: m[0].update(visual_revision=99))

    def test_stale_narration_revision_rejected(self):
        self.inventory_reject(lambda r, c, m: m[0].update(narration_revision=99))

    def test_unknown_mapping_policy_rejected(self):
        self.inventory_reject(lambda r, c, m: m[0].update(policy='foreign'))

    def test_semantic_obligation_removed_rejected(self):
        self.inventory_reject(lambda r, c, m: m[0]['source_obligations'].update(source_items=[]))

    def test_handoff_document_schema_confusion_rejected(self):
        self.node_reject(lambda h: h.update(schema_version='1.0.0'))

    def test_handoff_fingerprint_tamper_rejected(self):
        self.node_reject(lambda h: h.update(animation_plan_fingerprint='0'*64))

    def test_missing_start_rejected(self):
        self.node_reject(lambda h: h['nodes'][0].pop('start_ms'))

    def test_boolean_time_rejected(self):
        self.node_reject(lambda h: h['nodes'][0].update(start_ms=True))

    def test_coerced_time_rejected(self):
        self.node_reject(lambda h: h['nodes'][0].update(start_ms='0'))

    def test_nonfinite_time_rejected(self):
        self.node_reject(lambda h: h['nodes'][0].update(end_ms=float('inf')))

    def test_out_of_scene_rejected(self):
        self.node_reject(lambda h: h['nodes'][0].update(end_ms=self.scope['duration_ms']+1))

    def test_duplicate_track_rejected(self):
        self.node_reject(lambda h: h['nodes'].append(deepcopy(h['nodes'][0])))

    def test_unknown_target_rejected(self):
        self.node_reject(lambda h: h['nodes'][0].update(target_ids=['foreign']))

    def test_lost_parameter_rejected(self):
        self.node_reject(lambda h: h['nodes'][0]['parameters'].pop('easing'))

    def test_changed_easing_rejected(self):
        self.node_reject(lambda h: h['nodes'][0]['parameters'].update(easing='invented'))

    def test_invented_fallback_rejected(self):
        self.node_reject(lambda h: h['nodes'][0].update(fallback_action='enter'))

    def test_hidden_acceptance_rejected(self):
        self.node_reject(lambda h: h.update(accepted=True))

    def test_node_order_cannot_replace_target_identity(self):
        self.node_reject(lambda h: h['nodes'][0].update(target_ids=[self.catalog[0]['element_id']]))

    def test_audio_replan_preserved_by_complete_scene_admission(self):
        scene = replace(self.execution.timeline.scenes[0], requires_audio_replan=True)
        execution = replace(self.execution, timeline=replace(self.execution.timeline, scenes=(scene,)))
        with self.assertRaisesRegex(ProducerError, 'scene_ir_audio_replan_required'):
            scene_scope(execution, self.rows)

    def test_standard_and_reduced_native_selection_conserves_full_tracks(self):
        self.assertFalse(self.private['motion_selection']['standard']['standard_unresolved_references'])
        self.assertEqual(len(self.private['motion_selection']['reduced']['selected']), len(self.plan['tracks']))
        for preference in ('standard', 'reduced'):
            self.assertTrue(self.private['consumer_layout'][preference]['passed'])
            self.assertFalse(self.private['motion_selection'][preference]['accepted'])


if __name__ == '__main__':
    unittest.main()
