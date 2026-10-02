"""Ten exact original Batch002 capabilities; no repeated-run count inflation."""
from pathlib import Path
import sys, json, secrets, time, sqlite3, unittest, copy
from dataclasses import asdict
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(Path(__file__).parent))
from test_batch001 import Base
from batch002_fixtures import documents
from apps.operator.artifacts import ProductArtifacts,MAX_CODE
from apps.operator.contracts import Principal,PERMISSIONS,OperatorError
from apps.operator.service import Service
from apps.operator import view_contracts as vc
from bie.infrastructure.artifact_api import ArtifactAPI
from bie.infrastructure.evidence_api import EvidenceAPI

class ViewBase(Base):
    kind='reasoning'
    def setUp(self):
        super().setUp();self.art=ProductArtifacts(self.service);self.run=self.make_run()
        with self.service.catalog.tx() as db:_,self.body=self.service.catalog.intent(db,self.p,self.run)
        self.docs=documents(self.body);self.ref='source-'+self.body['native_job_id'][4:]
    def publish(self,payload=None):
        return self.art.publish(self.p,self.run,self.kind,payload if payload is not None else self.docs[self.kind],evidence_origin='SYNTHETIC_TEST')
    def view(self):return self.art.view(self.p,self.run,self.kind)
    def reject(self,payload):
        with self.assertRaises(OperatorError):self.publish(payload)
    def foreign(self):
        p=Principal('foreign','tenant-other',PERMISSIONS,time.time()+100)
        self.creds.grant(secrets.token_hex(32),p);return p
    def tamper_blob(self,aid):
        with self.service.native(self.body) as native:
            r=native.persistence.load_artifact(aid);path=native.data_root/'cas/blobs/sha256'/r.blob_digest[:2]/r.blob_digest
            raw=path.read_bytes();path.write_bytes(b'x'+raw[1:])

class Graph003(ViewBase):
    def test_decision_graph_and_canonical_validator(self):
        with patch.object(vc.re_contract.ReasoningDecisionGraph,'validate',autospec=True,wraps=None) as validate:
            self.publish()
        self.assertTrue(validate.called)
        v=self.view()['view'];self.assertEqual(v['edges'][0]['source'],'decision-a')
        self.assertEqual(v['nodes'][1]['status'],'ABSTAINED')
    def test_premises_confidence_uncertainty_evidence(self):
        v=self.publish()['view']['nodes'];self.assertTrue(v[0]['assumptions']);self.assertEqual(v[1]['confidence'],.45)
        self.assertTrue(v[1]['uncertainty']);self.assertEqual(v[0]['evidence_refs'][0]['artifact_id'],self.ref)
    def test_missing_reasoning_not_run(self):self.assertEqual(self.view()['status'],'NOT_RUN')
    def test_dependency_cycle_rejected(self):
        p=self.docs[self.kind];p['decisions'][0]['depends_on_decisions']=['decision-b'];self.reject(p)
    def test_missing_decision_parent_rejected(self):
        p=self.docs[self.kind];p['decisions'][1]['depends_on_decisions']=['absent'];self.reject(p)
    def test_low_confidence_cannot_claim_no_review(self):
        p=self.docs[self.kind];p['decisions'][1]['requires_review']=False;self.reject(p)
    def test_unknown_status_fails_closed(self):
        p=self.docs[self.kind];p['statuses']['decision-a']='PASS';self.reject(p)
    def test_cross_tenant_decision_view_rejected(self):
        self.publish();self.error(lambda:self.art.view(self.foreign(),self.run,self.kind),'run_not_found')
    def test_replay_restart_deterministic(self):
        a=self.publish();self.assertEqual(a,self.publish());self.assertEqual(a,ProductArtifacts(Service(self.root,self.creds)).view(self.p,self.run,self.kind))
    def test_missing_evidence_reference_rejected(self):
        p=self.docs[self.kind];p['decisions'][0]['evidence_refs'][0]['artifact_id']='missing';self.reject(p)
    def test_untrusted_html_stays_data(self):
        p=self.docs[self.kind];p['decisions'][0]['question']='<img src=x onerror=alert(1)>'
        self.assertEqual(self.publish()['view']['nodes'][0]['label'],p['decisions'][0]['question'])
    def test_http_projection_not_raw_payload(self):
        self.publish();r=self.get('runs/'+self.run+'/views/reasoning')
        self.assertEqual(r.status_code,200);self.assertNotIn('payload',r.json());self.assertFalse(r.json()['semantic_correctness_claimed'])
    def test_canonical_namespaced_subject_is_not_a_path(self):
        p=self.docs[self.kind];p['decisions'][0]['subject_id']='concept:coulomb'
        self.assertEqual(self.publish()['view']['nodes'][0]['subject'],'concept:coulomb')

class Lesson001(ViewBase):
    kind='curriculum'
    def test_actual_native_curriculum_optimizer_invoked(self):
        with patch.object(vc.curriculum,'optimize_book_curriculum',wraps=vc.curriculum.optimize_book_curriculum) as op:self.publish()
        self.assertGreaterEqual(op.call_count,1)
    def test_order_units_objectives_groups_and_timing(self):
        v=self.publish()['view'];self.assertEqual(tuple(v['order']),('unit-a','unit-b'));self.assertEqual(v['total_minutes'],18)
        self.assertTrue(v['units'][0]['objective_ids']);self.assertEqual(v['timing_basis'],'PLANNED_NOT_MEASURED')
    def test_stored_plan_edit_rejected(self):p=self.docs[self.kind];p['plan']['total_minutes']=999;self.reject(p)
    def test_dependency_cycle_rejected(self):
        p=self.docs[self.kind];p['dependencies'].append(dict(before='unit-b',after='unit-a',kind='prerequisite',hard=True,strength=1));self.reject(p)
    def test_oversized_collection_rejected(self):p=self.docs[self.kind];p['units']*=101;self.reject(p)
    def test_unknown_objective_field_rejected(self):p=self.docs[self.kind];p['units'][0]['secret']='hidden';self.reject(p)
    def test_false_number_is_not_metric(self):p=self.docs[self.kind];p['units'][0]['cognitive_load']=True;self.reject(p)
    def test_missing_artifact_not_fixture_substitution(self):self.assertEqual(self.view()['status'],'NOT_RUN')
    def test_read_requires_active_credential(self):
        self.publish();self.creds.revoke(self.token);self.error(lambda:self.view(),'unauthorized')
    def test_curriculum_evidence_binding(self):
        v=self.publish();e=self.art.evidence_detail(self.p,self.run,v['artifact_id']);self.assertEqual(e['evidence']['status'],'VALIDATED_NOT_ACCEPTED')

class Lesson002(ViewBase):
    kind='lesson'
    def test_canonical_architecture_and_pedagogy_invoked(self):
        with patch.object(vc,'build_lesson_architecture',wraps=vc.build_lesson_architecture) as a,patch.object(vc,'build_pedagogy_plan',wraps=vc.build_pedagogy_plan) as p:self.publish()
        self.assertTrue(a.called and p.called)
    def test_sections_timing_assessments_grounding(self):
        v=self.publish()['view'];self.assertEqual(len(v['sections']),2);self.assertEqual(v['duration_ms'],120000)
        self.assertTrue(v['assessments'][0]['success_criteria']);self.assertIn(self.body['source_id'],v['architecture']['source_ids'])
    def test_foreign_source_ids_rejected(self):p=self.docs[self.kind];p['architecture']['source_ids']=['foreign-source'];self.reject(p)
    def test_missing_assessment_rejected(self):p=self.docs[self.kind];p['assessments']=[];self.reject(p)
    def test_overlapping_sections_rejected(self):p=self.docs[self.kind];p['sections'][1]['start_ms']=100;self.reject(p)
    def test_undeclared_scene_rejected(self):p=self.docs[self.kind];p['sections'][0]['scene_id']='absent';self.reject(p)
    def test_pedagogy_review_cannot_be_weakened(self):p=self.docs[self.kind];p['pedagogy']['decisions'][0]['confidence']=.2;self.reject(p)
    def test_secret_in_generated_title_rejected(self):p=self.docs[self.kind];p['architecture']['title']='Bearer '+('x'*40);self.reject(p)
    def test_missing_lesson_not_run(self):self.assertEqual(self.view()['status'],'NOT_RUN')
    def test_http_lesson_view_is_structured(self):self.publish();self.assertIn('sections',self.get('runs/'+self.run+'/views/lesson').json()['view'])

class Lesson003(ViewBase):
    kind='director'
    def test_canonical_script_validation_invoked(self):
        with patch.object(vc,'validate_script_plan',wraps=vc.validate_script_plan) as v:self.publish()
        self.assertTrue(v.called)
    def test_timing_narration_visual_evidence(self):
        v=self.publish()['view'];self.assertEqual(v['timings'][0]['narration_refs'],['segment-a']);self.assertEqual(v['timings'][0]['visual_refs'],[self.ref])
    def test_missing_visual_evidence_rejected(self):p=self.docs[self.kind];p['timings'][0]['visual_refs']=['missing'];self.reject(p)
    def test_unknown_narration_ref_rejected(self):p=self.docs[self.kind];p['timings'][0]['narration_refs']=['unknown'];self.reject(p)
    def test_script_to_scene_binding_rejected(self):p=self.docs[self.kind];p['script_plan']['segments'][0]['scene_id']='unknown';self.reject(p)
    def test_overlapping_director_timing_rejected(self):p=self.docs[self.kind];p['timings'][1]['start_ms']=1;self.reject(p)
    def test_duplicate_scene_time_rejected(self):p=self.docs[self.kind];p['timings'][1]['scene_id']='scene-a';self.reject(p)
    def test_no_render_claim_from_plan(self):v=self.publish()['view'];self.assertFalse(v['compiled']);self.assertFalse(v['rendered'])
    def test_missing_plan_not_run(self):self.assertEqual(self.view()['status'],'NOT_RUN')
    def test_director_prerequisite_time_cannot_be_reversed(self):
        p=self.docs[self.kind];p['timings']=[dict(p['timings'][1],start_ms=0,end_ms=60000),dict(p['timings'][0],start_ms=60000,end_ms=120000)]
        self.reject(p)
    def test_source_artifact_tamper_blocks_director(self):
        self.publish();self.tamper_blob(self.ref)
        with self.assertRaises(ValueError):self.view()

class Lesson004(ViewBase):
    kind='scene_ir'
    def test_native_decode_and_accessibility_validation_called(self):
        with patch.object(vc,'decode_scene_ir',wraps=vc.decode_scene_ir) as d,patch.object(vc,'validate_accessibility',wraps=vc.validate_accessibility) as a:self.publish()
        self.assertTrue(d.called and a.called)
    def test_frames_boxes_viewport_are_structured(self):
        v=self.publish()['view'];self.assertEqual(v['tracks'][0]['end_frame_exclusive'],30);self.assertEqual(v['viewport']['width'],1920)
        self.assertIsNotNone(v['elements'][0]['box']);self.assertTrue(v['elements'][0]['accessibility'])
    def test_invalid_track_endpoint_rejected(self):p=self.docs[self.kind];p['document']['tracks'][0]['end_ms']=2000;self.reject(p)
    def test_element_outside_viewport_rejected(self):p=self.docs[self.kind];p['document']['elements'][0]['normalized_box']['x']=2;self.reject(p)
    def test_unknown_element_track_rejected(self):p=self.docs[self.kind];p['document']['tracks'][0]['element_id']='missing';self.reject(p)
    def test_accepted_true_rejected(self):p=self.docs[self.kind];p['document']['accepted']=True;self.reject(p)
    def test_private_path_in_asset_rejected(self):p=self.docs[self.kind];p['document']['elements'][0]['props']['asset']='C:/Users/private.png';self.reject(p)
    def test_boolean_fps_rejected(self):p=self.docs[self.kind];p['fps']=True;self.reject(p)
    def test_scene_ir_is_not_compiled_or_rendered(self):v=self.publish()['view'];self.assertFalse(v['compiled']);self.assertFalse(v['rendered']);self.assertFalse(v['accepted'])
    def test_missing_scene_ir_is_not_run(self):self.assertEqual(self.view()['status'],'NOT_RUN')
    def test_ir_fingerprint_tamper_rejected(self):p=self.docs[self.kind];p['document']['title']='Changed without re-signing';self.reject(p)

class Lesson005(ViewBase):
    kind='game_plan'
    def test_native_game_plan_validate_invoked(self):
        with patch.object(vc.game.DirectorPlan,'validate',wraps=vc.game.DirectorPlan.validate,autospec=True) as v:
            # autospec mock does not run the canonical body; independent next
            # call verifies the real serialized artifact contract too.
            self.publish()
        self.assertTrue(v.called);self.assertTrue(self.view()['view']['levels'])
    def test_mechanics_objectives_feedback_mastery_remediation(self):
        v=self.publish()['view'];self.assertTrue(v['levels']);self.assertTrue(v['feedback']);self.assertTrue(v['mastery_targets']);self.assertTrue(v['adaptations'])
    def test_game_plan_not_playable(self):v=self.publish()['view'];self.assertFalse(v['playable']);self.assertFalse(v['built']);self.assertFalse(v['product_accepted'])
    def test_unknown_wire_type_rejected(self):p=self.docs[self.kind];p['$type']='DangerousImportedClass';self.reject(p)
    def test_missing_game_level_rejected(self):p=self.docs[self.kind];p['levels']['$tuple']=[];self.reject(p)
    def test_product_acceptance_rejected(self):p=self.docs[self.kind];p['product_accepted']=True;self.reject(p)
    def test_quality_weakening_rejected(self):p=self.docs[self.kind];p['anti_slide_default']=False;self.reject(p)
    def test_game_provenance_hash_mismatch_rejected(self):
        p=self.docs[self.kind];p['objective_assignments']['$tuple'][0]['provenance']['refs']['$tuple'][0]['content_sha256']='0'*64;self.reject(p)
    def test_missing_game_plan_not_run(self):self.assertEqual(self.view()['status'],'NOT_RUN')
    def test_game_plan_deterministic_restart(self):
        a=self.publish();self.assertEqual(a,ProductArtifacts(Service(self.root,self.creds)).view(self.p,self.run,self.kind))
    def test_game_plan_stale_fingerprint_rejected(self):
        p=self.docs[self.kind];p['plan_fingerprint']='sha256:'+('0'*64);self.reject(p)

class Art001(ViewBase):
    def test_actual_persisted_artifacts_after_worker(self):
        self.service.work_once(self.p,self.run);rows=self.art.browse(self.p,self.run)['items']
        self.assertIn('document.inspection.safe_json',[r['artifact_type'] for r in rows])
    def test_pagination_has_no_duplicate_ids(self):
        self.publish();a=self.art.browse(self.p,self.run,limit=1);b=self.art.browse(self.p,self.run,offset=a['next_offset'],limit=100)
        self.assertNotIn(a['items'][0]['artifact_id'],[x['artifact_id'] for x in b['items']])
    def test_artifact_type_filter(self):
        self.publish();rows=self.art.browse(self.p,self.run,artifact_type='operator.view.reasoning')['items'];self.assertEqual(len(rows),1)
    def test_evidence_only_filter(self):self.publish();self.assertTrue(all(r['evidence'] for r in self.art.browse(self.p,self.run,evidence_only=True)['items']))
    def test_pagination_caps_enforced(self):self.error(lambda:self.art.browse(self.p,self.run,limit=101),'invalid_pagination')
    def test_foreign_run_inventory_hidden(self):self.error(lambda:self.art.browse(self.foreign(),self.run),'run_not_found')
    def test_no_source_content_route(self):self.assertEqual(self.get('runs/'+self.run+'/artifacts/'+self.ref+'/content').status_code,404)
    def test_metadata_does_not_expose_arbitrary_paths(self):
        with self.service.native(self.body) as native:
            record=native.persistence.load_artifact(self.ref)
            with native.persistence._conn() as db:
                db.execute("UPDATE artifact_records SET metadata_json=? WHERE artifact_id=?",(json.dumps({'path':'C:/private-user','secret':'hidden'}),self.ref))
        self.assertNotIn('private-user',json.dumps(self.art.browse(self.p,self.run)))
    def test_catalog_binding_tampering_detected(self):
        self.publish()
        with sqlite3.connect(self.service.catalog.path) as db:db.execute("UPDATE graphs SET sha=?",('0'*64,))
        self.error(lambda:self.art.browse(self.p,self.run),'catalog_state_tampered')
    def test_filter_rejects_path_traversal(self):self.error(lambda:self.art.browse(self.p,self.run,artifact_type='../source'),'invalid_filter')

class Art002(ViewBase):
    def test_canonical_artifact_api_lineage_invoked(self):
        v=self.publish()
        original=ArtifactAPI.lineage;calls=[]
        def call(api,key):calls.append(key);return original(api,key)
        with patch.object(ArtifactAPI,'lineage',call):lineage=self.art.lineage(self.p,self.run,v['artifact_id'])
        self.assertTrue(calls);self.assertIn(self.ref,lineage['roots'])
    def test_parent_child_direction_and_roots(self):
        v=self.publish();g=self.art.lineage(self.p,self.run,v['artifact_id']);self.assertIn(dict(source=self.ref,target=v['artifact_id'],type='parent_of'),g['edges'])
    def test_bounded_lineage_explicit_failure(self):
        self.publish();self.error(lambda:self.art.lineage(self.p,self.run,self.ref,max_nodes=1),'lineage_limit')
    def test_cycle_in_native_parent_inventory_rejected(self):
        with self.service.native(self.body) as native:
            with native.persistence._conn() as db:db.execute('INSERT INTO artifact_parents(artifact_id,parent_artifact_id) VALUES(?,?)',(self.ref,self.ref))
        self.error(lambda:self.art.lineage(self.p,self.run,self.ref),'lineage_cycle')
    def test_missing_parent_fails_closed(self):
        with self.service.native(self.body) as native:
            with native.persistence._conn() as db:db.execute('INSERT INTO artifact_parents(artifact_id,parent_artifact_id) VALUES(?,?)',(self.ref,'missing'))
        self.error(lambda:self.art.lineage(self.p,self.run,self.ref),'artifact_parent_invalid')
    def test_corrupted_blob_rejected(self):
        v=self.publish();self.tamper_blob(v['artifact_id'])
        with self.assertRaises(ValueError):self.art.lineage(self.p,self.run,v['artifact_id'])
    def test_record_parent_tamper_detected_by_seal(self):
        v=self.publish()
        with self.service.native(self.body) as native:
            with native.persistence._conn() as db:db.execute('DELETE FROM artifact_parents WHERE artifact_id=?',(v['artifact_id'],))
        self.error(lambda:self.view(),'artifact_record_tampered')
    def test_foreign_lineage_rejected(self):self.error(lambda:self.art.lineage(self.foreign(),self.run,self.ref),'run_not_found')
    def test_lineage_survives_restart(self):
        v=self.publish();a=self.art.lineage(self.p,self.run,v['artifact_id']);self.assertEqual(a,ProductArtifacts(Service(self.root,self.creds)).lineage(self.p,self.run,v['artifact_id']))
    def test_unknown_artifact_rejected(self):self.error(lambda:self.art.lineage(self.p,self.run,'absent'),'artifact_not_found')

class Art003(ViewBase):
    def test_canonical_evidence_api_invoked(self):
        v=self.publish();orig=EvidenceAPI.get;calls=[]
        def call(api,key):calls.append(key);return orig(api,key)
        with patch.object(EvidenceAPI,'get',call):self.art.evidence_detail(self.p,self.run,v['artifact_id'])
        self.assertTrue(calls)
    def test_fixture_evidence_does_not_claim_live(self):
        v=self.publish();e=self.art.evidence_detail(self.p,self.run,v['artifact_id']);self.assertTrue(e['fixture_evidence']);self.assertEqual(e['origin'],'SYNTHETIC_TEST')
    def test_signatures_reviewer_state_not_fabricated(self):
        v=self.publish();e=self.art.evidence_detail(self.p,self.run,v['artifact_id']);self.assertFalse(e['signature_verified']);self.assertEqual(e['reviewer_state'],'UNATTESTED')
    def test_actual_worker_evidence_is_safe(self):
        self.service.work_once(self.p,self.run);rows=self.art.browse(self.p,self.run,evidence_only=True)['items']
        e=self.art.evidence_detail(self.p,self.run,rows[0]['artifact_id']);self.assertEqual(e['evidence']['source_hash'],self.body['source_hash'])
    def test_source_is_not_evidence(self):self.error(lambda:self.art.evidence_detail(self.p,self.run,self.ref),'evidence_not_found')
    def test_corrupted_evidence_rejected(self):
        v=self.publish();self.tamper_blob(v['artifact_id'])
        with self.assertRaises(ValueError):self.art.evidence_detail(self.p,self.run,v['artifact_id'])
    def test_cross_run_evidence_rejected(self):
        v=self.publish();other=self.make_run('other');self.error(lambda:self.art.evidence_detail(self.p,other,v['artifact_id']),'evidence_not_found')
    def test_unknown_evidence_not_found(self):self.error(lambda:self.art.evidence_detail(self.p,self.run,'unknown'),'evidence_not_found')
    def test_evidence_http_is_safe_structured(self):
        v=self.publish();r=self.get('runs/'+self.run+'/artifacts/'+v['artifact_id']+'/evidence');self.assertEqual(r.status_code,200);self.assertNotIn('payload',r.json())
    def test_no_http_producer_publish(self):self.assertEqual(self.post('runs/'+self.run+'/views/reasoning',self.docs['reasoning']).status_code,405)

class Art004(ViewBase):
    def code(self,value='print("synthetic generated code")\n',language='python'):
        return self.art.publish_code(self.p,self.run,value,language,evidence_origin='SYNTHETIC_TEST')
    def test_code_native_cas_hash_and_language(self):
        aid=self.code();r=self.art.code(self.p,self.run,aid);self.assertEqual(r['language'],'python');self.assertEqual(r['integrity'],'VERIFIED');self.assertEqual(len(r['sha256']),64)
    def test_line_number_pagination(self):
        aid=self.code('a\nb\nc\n');r=self.art.code(self.p,self.run,aid,limit=2);self.assertEqual(r['next_offset'],2)
        self.assertEqual(self.art.code(self.p,self.run,aid,offset=2)['lines'],[dict(number=3,text='c')])
    def test_code_not_executed(self):
        aid=self.code('raise RuntimeError("must not execute")');self.assertFalse(self.art.code(self.p,self.run,aid)['executed'])
    def test_html_in_code_is_literal_data(self):
        source='<script>window.evil=1</script>';aid=self.code(source,'html');self.assertEqual(self.art.code(self.p,self.run,aid)['lines'][0]['text'],source)
    def test_raw_source_cannot_open_as_code(self):self.error(lambda:self.art.code(self.p,self.run,self.ref),'code_artifact_not_found')
    def test_oversized_code_rejected(self):self.error(lambda:self.code('x'*(MAX_CODE+1)),'code_size_limit')
    def test_unknown_language_rejected(self):self.error(lambda:self.code('a','executable_binary'),'code_language_unsupported')
    def test_credential_text_cannot_be_persisted(self):self.error(lambda:self.code('Bearer '+('x'*40)),'private_data_rejected')
    def test_corrupted_generated_code_fails_closed(self):
        aid=self.code();self.tamper_blob(aid)
        with self.assertRaises(ValueError):self.art.code(self.p,self.run,aid)
    def test_code_foreign_tenant_hidden(self):aid=self.code();self.error(lambda:self.art.code(self.foreign(),self.run,aid),'run_not_found')
    def test_code_replay_immutable_parent_set(self):
        aid=self.code();other=self.publish()['artifact_id']
        self.error(lambda:self.art.publish_code(self.p,self.run,'print("synthetic generated code")\n','python',evidence_origin='SYNTHETIC_TEST',parent_refs=[other]),'code_immutable_conflict')
    def test_safe_error_has_no_internal_details(self):
        aid=self.code();self.tamper_blob(aid);r=self.get('runs/'+self.run+'/artifacts/'+aid+'/code')
        self.assertEqual(r.status_code,500);self.assertNotIn(str(self.root),r.text)
    def test_restart_code_display_survives(self):aid=self.code();self.assertEqual(self.art.code(self.p,self.run,aid),ProductArtifacts(Service(self.root,self.creds)).code(self.p,self.run,aid))
    def test_partial_native_code_publish_recoverable(self):
        with patch.object(self.service.catalog,'event',side_effect=RuntimeError('interrupted_after_native_write')):
            with self.assertRaises(RuntimeError):self.code()
        aid=self.code();self.assertEqual(self.art.code(self.p,self.run,aid)['integrity'],'VERIFIED')
    def test_publish_permission_required(self):
        p=Principal('reader','tenant-a',frozenset({'read'}),time.time()+100);self.creds.grant(secrets.token_hex(32),p)
        self.error(lambda:self.art.publish_code(p,self.run,'x','python',evidence_origin='SYNTHETIC_TEST'),'forbidden')
    def test_code_lines_are_bounded_and_fully_addressable(self):self.error(lambda:self.code('x\n'*10001),'code_line_limit')

TASK_CLASSES={'BIE-APP-GRAPH-003':Graph003,**{'BIE-APP-LESSON-'+str(i).zfill(3):globals()['Lesson'+str(i).zfill(3)] for i in range(1,6)},
              **{'BIE-APP-ART-'+str(i).zfill(3):globals()['Art'+str(i).zfill(3)] for i in range(1,5)}}
def selected_suite(task=None):
    suite=unittest.TestSuite()
    for cls in (TASK_CLASSES.values() if task is None else [TASK_CLASSES[task]]):
        for name in sorted(n for n in cls.__dict__ if n.startswith('test_')):suite.addTest(cls(name))
    return suite
if __name__=='__main__':raise SystemExit(not unittest.TextTestRunner(verbosity=2).run(selected_suite()).wasSuccessful())
