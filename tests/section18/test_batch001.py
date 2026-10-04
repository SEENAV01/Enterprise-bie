"""Section 18 Batch 001. Synthetic fixtures are NOT real-book acceptance."""
from pathlib import Path
import asyncio, gc, hashlib, json, os, secrets, socket, sqlite3, subprocess, sys, tempfile, time, unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/'tests/productization/document_intelligence'))
from fastapi.testclient import TestClient
from apps.operator.contracts import Credentials,Principal,PERMISSIONS,OperatorError,canonical,private_path
from apps.operator.service import Service
from apps.operator.main import create_app
from bie.infrastructure.run_api import RunAPI
from bie.infrastructure.artifact_store import FileSystemCAS
from bie.document_intelligence.real_pdf_toc_runtime import RealPdfTocRuntimeError
from structural_pdf_fixtures import hierarchy_pdf_with_outline,structural_pdf

DATA=hierarchy_pdf_with_outline()
SHA=hashlib.sha256(DATA).hexdigest()

class Base(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='bie-app18-')
        self.root=Path(self.tmp.name)
        self.creds=Credentials();self.token=secrets.token_hex(32)
        self.p=Principal('test-operator','tenant-a',PERMISSIONS,time.time()+3600)
        self.creds.grant(self.token,self.p)
        self.service=Service(self.root,self.creds)
        self.client=TestClient(create_app(self.service),base_url='http://localhost',raise_server_exceptions=False)
        self.headers={'Authorization':'Bearer '+self.token}
    def tearDown(self):
        self.client.close();gc.collect();self.tmp.cleanup()
    def source(self,data=DATA): return self.service.import_pdf(self.p,data)
    def make_run(self,key='test-run'):
        return self.service.create(self.p,self.source()['source_id'],{},key)['run_id']
    def get(self,path,**kwargs): return self.client.get('/operator/v1/'+path,headers=self.headers,**kwargs)
    def post(self,path,value): return self.client.post('/operator/v1/'+path,headers=self.headers,json=value)
    def error(self,fn,code):
        with self.assertRaises(OperatorError) as ctx:fn()
        self.assertEqual(ctx.exception.code,code)
    def http(self,run,action,revision):return self.post('runs/'+run+'/control',dict(action=action,expected_revision=revision))

class Run001(Base):
    def test_native_runapi_is_executed(self):
        original=RunAPI.create
        calls=[]
        def invoke(api,req): calls.append(req);return original(api,req)
        with patch.object(RunAPI,'create',invoke):run=self.make_run()
        self.assertEqual(len(calls),1);self.assertEqual(len(calls[0].config_hash),64)
        self.assertEqual(self.service.status(self.p,run)['engine_state'],'READY')
    def test_restart_keeps_identity(self):
        run=self.make_run();self.service=Service(self.root,self.creds)
        self.assertEqual(self.make_run(),run)
    def test_same_key_different_config_conflicts(self):
        source=self.source()['source_id'];self.service.create(self.p,source,{},'key')
        self.error(lambda:self.service.create(self.p,source,{'locale':'hi'},'key'),'idempotency_conflict')
    def test_same_key_different_source_conflicts(self):
        self.make_run('key');source=self.source(structural_pdf(2))['source_id']
        self.error(lambda:self.service.create(self.p,source,{},'key'),'idempotency_conflict')
    def test_invalid_source_cannot_create_run(self):
        source=self.source(b'not-pdf')['source_id']
        self.error(lambda:self.service.create(self.p,source,{},'key'),'source_not_valid')
    def test_engine_profile_unavailable_not_fake_ready(self):
        self.error(lambda:self.service.create(self.p,self.source()['source_id'],{'profile':'book_to_video'},'key'),
                   'engine_profile_unavailable')
    def test_canonical_config_is_persisted(self):
        run=self.make_run();state=self.service.status(self.p,run)
        with self.service.catalog.tx() as db:_,body=self.service.catalog.intent(db,self.p,run)
        with self.service.native(body) as native:
            rows=[native.persistence.load_artifact(a) for a in native.persistence.artifacts_for_run(body['native_job_id'])]
        self.assertEqual(sum(r.artifact_type=='operator.run.config' for r in rows),1)
        self.assertTrue(all(x['status']=='NOT_RUN' for x in state['learning_outputs'].values()))
    def test_strict_config_rejects_bool_output_and_unknown_fields(self):
        source=self.source()['source_id']
        for config in ({'outputs':[True]},{'outputs':[[]]},{'unknown':1},{'locale':'unsupported'},{'model_policy':'quality_first'}):
            with self.subTest(config=config):
                with self.assertRaises(OperatorError):self.service.create(self.p,source,config,'key')
    def test_create_http_202_is_real_persisted(self):
        response=self.post('runs',dict(source_id=self.source()['source_id'],config={},idempotency_key='key'))
        self.assertEqual(response.status_code,202)
        self.assertEqual(self.get('runs/'+response.json()['run_id']).json()['status'],'READY')
    def test_no_create_permission(self):
        p=Principal('reader','tenant-a',frozenset({'read'}),time.time()+100)
        self.creds.grant(secrets.token_hex(32),p)
        self.error(lambda:self.service.create(p,self.source()['source_id'],{},'key'),'forbidden')
    def test_index_tampering_fails_closed(self):
        run=self.make_run()
        with sqlite3.connect(self.service.catalog.path) as db:db.execute("UPDATE intents SET control='CANCELLED'")
        self.error(lambda:self.service.status(self.p,run),'catalog_state_tampered')
    def test_request_no_credentials(self):
        r=self.client.post('/operator/v1/runs',json={})
        self.assertEqual(r.status_code,401)
    def test_partial_native_submit_recovers_idempotently(self):
        source=self.source()['source_id']
        with patch.object(self.service,'_register',side_effect=RuntimeError('seeded_interruption')):
            with self.assertRaises(RuntimeError):self.service.create(self.p,source,{},'recover')
        recovered=Service(self.root,self.creds).create(self.p,source,{},'recover')
        self.assertEqual(self.service.status(self.p,recovered['run_id'])['queue_state'],'READY')
        self.assertEqual(self.service.work_once(self.p,recovered['run_id'])['outcome'],'ACKED')
    def test_concurrent_idempotent_create_one_run(self):
        from concurrent.futures import ThreadPoolExecutor
        source=self.source()['source_id']
        with ThreadPoolExecutor(max_workers=3) as pool:
            values=list(pool.map(lambda _:self.service.create(self.p,source,{},'concurrent'),range(3)))
        self.assertEqual(len({r['run_id'] for r in values}),1)
        self.assertEqual(len(self.service.list_runs(self.p)['items']),1)

class Run002(Base):
    def upload(self,data=DATA,media='application/pdf',headers=None):
        return self.client.post('/operator/v1/sources',content=data,headers={**self.headers,'Content-Type':media,**(headers or {})})
    def test_upload_streams_hashes_and_uses_canonical_cas(self):
        with patch.object(FileSystemCAS,'put_bytes',autospec=True,side_effect=FileSystemCAS.put_bytes) as put:
            r=self.upload()
        self.assertEqual(r.status_code,200);self.assertEqual(r.json()['sha256'],SHA);self.assertEqual(put.call_count,1)
    def test_duplicate_detected_and_not_added(self):
        first=self.upload().json();second=self.upload().json()
        self.assertFalse(first['duplicate']);self.assertTrue(second['duplicate'])
        self.assertEqual(first['source_id'],second['source_id'])
    def test_oversized_declared_body_rejected(self):
        self.service.limit=8
        self.assertEqual(self.upload(b'123456789').status_code,413)
        self.assertEqual(list((self.root/'staging').iterdir()),[])
    def test_streamed_limit_without_length(self):
        self.service.limit=8
        r=self.upload(iter([b'12345',b'67890']))
        self.assertEqual(r.status_code,413);self.assertEqual(list((self.root/'staging').iterdir()),[])
    def test_exact_limit_allowed(self):
        self.service.limit=len(DATA);self.assertEqual(self.upload().status_code,200)
    def test_empty_body_rejected(self):self.assertEqual(self.upload(b'').status_code,400)
    def test_wrong_media_type_rejected(self):self.assertEqual(self.upload(media='image/png').status_code,415)
    def test_pdf_parameters_allowed(self):self.assertEqual(self.upload(media='application/pdf; charset=binary').status_code,200)
    def test_client_filename_never_selects_path(self):
        r=self.upload(headers={'X-Filename':'../../secret.pdf'})
        self.assertEqual(r.status_code,200);self.assertNotIn('secret.pdf',r.text)
        self.assertFalse((self.root/'secret.pdf').exists())
    def test_invalid_source_does_not_store_bytes(self):
        r=self.upload(b'SECRET-invalid-source')
        self.assertEqual(r.status_code,200);self.assertFalse(r.json()['stored']);self.assertNotIn('SECRET',r.text)
    def test_source_cas_corruption_prevents_run(self):
        source=self.source()
        path=self.root/'sources-cas/blobs/sha256'/SHA[:2]/SHA
        # Seeded fault, confined test storage only.
        path.write_bytes(b'corrupt')
        with self.assertRaises(Exception):self.service.create(self.p,source['source_id'],{},'key')
    def test_unauthorized_upload_not_persisted(self):
        r=self.client.post('/operator/v1/sources',content=DATA,headers={'Content-Type':'application/pdf'})
        self.assertEqual(r.status_code,401)
        with self.service.catalog.tx() as db:self.assertEqual(db.execute('SELECT COUNT(*) FROM sources').fetchone()[0],0)
    def test_trusted_relative_root_normalizes_without_path_escape(self):
        self.assertEqual(private_path(self.root/'nested/..'),self.root)
    def test_client_style_parent_escape_rejected(self):
        with self.assertRaises(PermissionError):private_path(self.root,'..','outside')

class Run003(Base):
    def test_source_valid_metadata(self):
        s=self.source();self.assertEqual(s['validation']['status'],'VALID');self.assertEqual(s['validation']['page_count'],5)
    def test_invalid_metadata_safe_codes(self):
        s=self.source(b'bad');self.assertEqual(s['validation']['status'],'INVALID')
        self.assertEqual(s['validation']['diagnostic_codes'],['pdf_validation_failed'])
    def test_encrypted_pdf_invalid(self):
        from io import BytesIO
        from pypdf import PdfWriter
        w=PdfWriter();w.add_blank_page(width=612,height=792);w.encrypt('do-not-print');out=BytesIO();w.write(out)
        s=self.source(out.getvalue());self.assertEqual(s['validation']['status'],'INVALID')
    def test_validation_survives_restart(self):
        s=self.source();second=Service(self.root,self.creds)
        self.assertEqual(second.source(self.p,s['source_id'])['validation'],s['validation'])
    def test_source_metadata_never_leaks_headings(self):
        r=self.get('sources/'+self.source()['source_id'])
        self.assertNotIn('CHAPTER 1 Foundation',r.text);self.assertNotIn('Ordinary hierarchy',r.text)
    def test_unknown_source_404(self):self.assertEqual(self.get('sources/missing').status_code,404)
    def test_foreign_tenant_source_404(self):
        p=Principal('other','tenant-b',PERMISSIONS,time.time()+100);self.creds.grant(secrets.token_hex(32),p)
        self.error(lambda:self.service.source(p,self.source()['source_id']),'source_not_found')
    def test_ui_shows_valid_invalid_and_blocks_create(self):
        html=self.client.get('/').text;js=self.client.get('/static/operator.js').text
        self.assertIn('Import &amp; validate',html);self.assertIn("source.validation.status!=='VALID'",js)
    def test_invalid_json_duplicate_keys_rejected(self):
        r=self.client.post('/operator/v1/runs',headers={**self.headers,'Content-Type':'application/json'},
            content=b'{"source_id":"a","source_id":"b"}')
        self.assertEqual(r.status_code,400);self.assertEqual(r.json()['error']['code'],'duplicate_json_key')
    def test_source_record_tampering_rejected(self):
        s=self.source()
        with sqlite3.connect(self.service.catalog.path) as db:db.execute("UPDATE sources SET body='{}'")
        self.error(lambda:self.service.source(self.p,s['source_id']),'catalog_state_tampered')

class Run004(Base):
    def test_ready_comes_from_native_queue(self):
        run=self.make_run();state=self.service.status(self.p,run)
        self.assertEqual((state['status'],state['queue_state']),('READY','READY'))
    def test_canonical_worker_success_is_persisted(self):
        run=self.make_run();out=self.service.work_once(self.p,run)
        self.assertEqual(out['outcome'],'ACKED')
        self.assertEqual(self.service.status(self.p,run)['status'],'SUCCEEDED')
    def test_success_survives_service_restart(self):
        run=self.make_run();self.service.work_once(self.p,run)
        self.assertEqual(Service(self.root,self.creds).status(self.p,run)['queue_state'],'ACKED')
    def test_result_matches_source_hash(self):
        run=self.make_run();self.service.work_once(self.p,run)
        self.assertEqual(self.service.result(self.p,run)['source_hash'],SHA)
    def test_no_percentage_and_no_product_acceptance(self):
        r=self.get('runs/'+self.make_run())
        self.assertNotIn('percent',r.text);self.assertFalse(r.json()['product_accepted'])
    def test_list_pagination_and_tenant_filter(self):
        first=self.make_run('first');second=self.make_run('second')
        page=self.service.list_runs(self.p,limit=1)
        self.assertEqual(len(page['items']),1);self.assertEqual(page['next_offset'],1)
        self.assertEqual(len(self.service.list_runs(self.p,1,1)['items']),1)
    def test_invalid_pagination_rejected(self):
        self.error(lambda:self.service.list_runs(self.p,-1,1),'invalid_pagination')
        self.error(lambda:self.service.list_runs(self.p,0,101),'invalid_pagination')
    def test_revoked_token_cannot_read(self):
        run=self.make_run();self.creds.revoke(self.token)
        self.assertEqual(self.get('runs/'+run).status_code,401)
    def test_expired_token_rejected(self):
        t=secrets.token_hex(32);self.creds.grant(t,Principal('expired','tenant-a',PERMISSIONS,time.time()-1))
        r=self.client.get('/operator/v1/runs',headers={'Authorization':'Bearer '+t});self.assertEqual(r.status_code,401)
    def test_foreign_run_not_leaked(self):
        run=self.make_run();t=secrets.token_hex(32)
        self.creds.grant(t,Principal('other','tenant-b',PERMISSIONS,time.time()+100))
        r=self.client.get('/operator/v1/runs/'+run,headers={'Authorization':'Bearer '+t});self.assertEqual(r.status_code,404)
    def test_result_cas_tamper_fails_closed(self):
        run=self.make_run();self.service.work_once(self.p,run)
        with self.service.catalog.tx() as db:_,body=self.service.catalog.intent(db,self.p,run)
        with self.service.native(body) as native:
            rec=native.persistence.load_artifact('result-'+body['native_job_id'][4:])
            path=native.data_root/'cas/blobs/sha256'/rec.blob_digest[:2]/rec.blob_digest
            raw=path.read_bytes();changed=raw.replace(b'"page_count":5',b'"page_count":6')
            self.assertNotEqual(raw,changed);self.assertEqual(len(raw),len(changed));path.write_bytes(changed)
        self.assertEqual(self.get('runs/'+run).status_code,500)
    def test_native_execution_not_duplicate_on_second_worker(self):
        run=self.make_run();self.service.work_once(self.p,run)
        self.assertFalse(self.service.work_once(self.p,run)['dispatched'])
    def test_native_stage_row_without_matching_event_rejected(self):
        run=self.make_run()
        with sqlite3.connect(self.root/'runs'/run/'runs.sqlite3') as db:db.execute("UPDATE attempts SET state='RUNNING'")
        self.error(lambda:self.service.status(self.p,run),'native_transition_history_inconsistent')

class Run005(Base):
    def test_ordered_native_events(self):
        run=self.make_run();self.service.work_once(self.p,run)
        items=self.service.timeline(self.p,run)['items']
        native=[e for e in items if e['event_origin']=='CANONICAL_PERSISTENCE']
        self.assertEqual([e['to_state'] for e in native],['READY','RUNNING','SUCCEEDED'])
    def test_attempt_and_evidence_references(self):
        run=self.make_run();self.service.work_once(self.p,run)
        last=[e for e in self.service.timeline(self.p,run)['items'] if e['to_state']=='SUCCEEDED'][0]
        self.assertEqual(last['attempt'],1);self.assertTrue(last['evidence_refs'])
    def test_real_timestamps_are_present(self):
        from datetime import datetime
        for e in self.service.timeline(self.p,self.make_run())['items']:self.assertIsNotNone(datetime.fromisoformat(e['timestamp']).tzinfo)
    def test_control_events_retained(self):
        run=self.make_run();self.service.control(self.p,run,'pause',1);self.service.control(self.p,run,'resume',2)
        actions=[e['to_state'] for e in self.service.timeline(self.p,run)['items']]
        self.assertIn('RUN_PAUSED',actions);self.assertIn('RUN_READY',actions)
    def test_after_cursor_no_duplicate_events(self):
        run=self.make_run();a=self.service.timeline(self.p,run,limit=1);b=self.service.timeline(self.p,run,after=a['next_after'])
        self.assertTrue(all(e['timeline_order']>a['next_after'] for e in b['items']))
    def test_restart_timeline_unchanged(self):
        run=self.make_run();a=self.service.timeline(self.p,run)
        self.assertEqual(a,Service(self.root,self.creds).timeline(self.p,run))
    def test_native_reason_is_redacted(self):
        run=self.make_run()
        with self.service.catalog.tx() as db:_,body=self.service.catalog.intent(db,self.p,run)
        with sqlite3.connect(self.root/'runs'/run/'runs.sqlite3') as db:db.execute("UPDATE transition_events SET reason='secret internal stack'")
        self.assertNotIn('secret internal',json.dumps(self.service.timeline(self.p,run)))
    def test_history_deletion_detected(self):
        run=self.make_run()
        with sqlite3.connect(self.service.catalog.path) as db:db.execute('DELETE FROM audit')
        with self.assertRaises(OperatorError):self.service.timeline(self.p,run)
    def test_timeline_http_has_safe_native_evidence(self):
        run=self.make_run();self.assertEqual(self.get('runs/'+run+'/timeline').status_code,200)

class Run006(Base):
    def fail(self):
        run=self.make_run()
        with patch('apps.api.job_service.inspect_real_pdf_toc',side_effect=RealPdfTocRuntimeError('PRIVATE-pdf-detail')):
            self.service.work_once(self.p,run)
        return run
    def test_failure_comes_from_native_worker(self):
        run=self.fail();self.assertEqual(self.service.status(self.p,run)['status'],'FAILED')
    def test_safe_failure_code_and_evidence(self):
        run=self.fail();f=self.service.failure(self.p,run)
        self.assertEqual(f['diagnostic_codes'],['pdf_inspection_failed']);self.assertTrue(f['evidence_refs'])
    def test_unexpected_failure_has_no_secret(self):
        run=self.make_run()
        with patch('apps.api.job_service.inspect_real_pdf_toc',side_effect=RuntimeError('SECRET-KEY traceback C:/private')):
            self.service.work_once(self.p,run)
        r=self.get('runs/'+run+'/failure')
        self.assertEqual(r.status_code,200);self.assertNotIn('SECRET-KEY',r.text);self.assertNotIn('traceback',r.text.replace('traceback_exposed',''))
    def test_failure_view_ready_not_available(self):self.assertEqual(self.get('runs/'+self.make_run()+'/failure').status_code,409)
    def test_result_failed_rejected(self):self.assertEqual(self.get('runs/'+self.fail()+'/result').status_code,409)
    def test_failure_survives_restart(self):
        run=self.fail();self.assertEqual(Service(self.root,self.creds).failure(self.p,run)['status'],'FAILED')
    def test_failure_details_arbitrary_diagnostic_redacted(self):
        run=self.fail()
        with sqlite3.connect(self.root/'runs'/run/'runs.sqlite3') as db:
            db.execute("UPDATE attempts SET diagnostics_json='[\"SECRET\"]'")
        self.assertEqual(self.service.failure(self.p,run)['diagnostic_codes'],['diagnostic_redacted'])
    def test_error_http_no_unexpected_exception_details(self):
        with patch.object(self.service,'list_runs',side_effect=RuntimeError('private-path')):
            r=self.get('runs')
        self.assertEqual(r.status_code,500);self.assertNotIn('private-path',r.text)
    def test_queue_dead_letter_failure_is_truthful(self):
        self.assertEqual(self.service.status(self.p,self.fail())['queue_state'],'DEAD_LETTER')
    def test_failure_evidence_navigation_delegates_native_api(self):
        run=self.fail();ref=self.service.failure(self.p,run)['evidence_refs'][0]
        evidence=self.service.evidence(self.p,run,ref)
        self.assertEqual(evidence['evidence']['diagnostic_code'],'pdf_inspection_failed')
        self.assertEqual(self.get('runs/'+run+'/evidence/'+ref).status_code,200)
    def test_foreign_evidence_not_accessible(self):
        run=self.fail();other=self.make_run('other');ref=self.service.failure(self.p,run)['evidence_refs'][0]
        self.assertEqual(self.get('runs/'+other+'/evidence/'+ref).status_code,404)

class Run007(Run006):
    # Inherited helper only; test methods are restricted by runner for this class.
    def test_retry_creates_new_child_preserves_parent(self):
        parent=self.fail();before=self.service.timeline(self.p,parent)
        child=self.service.retry(self.p,parent,'retry')['run_id']
        self.assertNotEqual(parent,child);self.assertEqual(self.service.status(self.p,child)['parent_run_id'],parent)
        self.assertEqual(self.service.timeline(self.p,parent),before)
    def test_retry_replay_same_child(self):
        parent=self.fail();a=self.service.retry(self.p,parent,'retry');b=self.service.retry(self.p,parent,'retry')
        self.assertEqual(a['run_id'],b['run_id']);self.assertTrue(b['replayed'])
    def test_retry_native_child_executes(self):
        parent=self.fail();child=self.service.retry(self.p,parent,'retry')['run_id'];self.service.work_once(self.p,child)
        self.assertEqual(self.service.status(self.p,child)['status'],'SUCCEEDED')
        self.assertEqual(self.service.status(self.p,parent)['status'],'FAILED')
    def test_retry_ready_run_rejected(self):self.error(lambda:self.service.retry(self.p,self.make_run(),'retry'),'retry_requires_failed_parent')
    def test_retry_without_permission_rejected(self):
        parent=self.fail();p=Principal('reader','tenant-a',frozenset({'read'}),time.time()+100)
        self.creds.grant(secrets.token_hex(32),p)
        self.error(lambda:self.service.retry(p,parent,'retry'),'forbidden')
    def test_lineage_manifest_is_canonical_cas_artifact(self):
        parent=self.fail();child=self.service.retry(self.p,parent,'retry')['run_id']
        with self.service.catalog.tx() as db:_,body=self.service.catalog.intent(db,self.p,child)
        with self.service.native(body) as native:
            types=[native.persistence.load_artifact(a).artifact_type for a in native.persistence.artifacts_for_run(body['native_job_id'])]
        self.assertIn('operator.run.lineage',types)
    def test_retry_endpoint_202(self):self.assertEqual(self.post('runs/'+self.fail()+'/retry',{'idempotency_key':'retry'}).status_code,202)
    def test_retry_after_restart_same_identity(self):
        parent=self.fail();a=self.service.retry(self.p,parent,'retry')['run_id']
        b=Service(self.root,self.creds).retry(self.p,parent,'retry')['run_id'];self.assertEqual(a,b)

class Run008(Base):
    def test_pause_stops_real_dispatch_not_just_ui(self):
        run=self.make_run();self.service.control(self.p,run,'pause',1)
        with patch('apps.api.job_service.PdfInspectionJobService.run_once') as dispatch:
            self.assertEqual(self.service.work_once(self.p,run)['outcome'],'PAUSED')
        dispatch.assert_not_called();state=self.service.status(self.p,run)
        self.assertEqual((state['status'],state['engine_state'],state['queue_state']),('PAUSED','READY','READY'))
    def test_resume_allows_canonical_worker(self):
        run=self.make_run();self.service.control(self.p,run,'pause',1);self.service.control(self.p,run,'resume',2)
        self.assertEqual(self.service.work_once(self.p,run)['outcome'],'ACKED')
    def test_cancel_dead_letters_queue_and_blocks_stage(self):
        run=self.make_run();self.service.control(self.p,run,'cancel',1);state=self.service.status(self.p,run)
        self.assertEqual((state['status'],state['engine_state'],state['queue_state']),('CANCELLED','BLOCKED','DEAD_LETTER'))
        self.assertFalse(self.service.work_once(self.p,run)['dispatched'])
    def test_stale_revision_cannot_change_state(self):
        run=self.make_run();self.service.control(self.p,run,'pause',1)
        self.error(lambda:self.service.control(self.p,run,'cancel',1),'stale_revision')
        self.assertEqual(self.service.status(self.p,run)['status'],'PAUSED')
    def test_terminal_control_cannot_rewrite_success(self):
        run=self.make_run();self.service.work_once(self.p,run)
        self.error(lambda:self.service.control(self.p,run,'cancel',1),'running_or_terminal_control_unavailable')
        self.assertEqual(self.service.status(self.p,run)['status'],'SUCCEEDED')
    def test_running_control_fails_closed(self):
        run=self.make_run()
        with self.service.catalog.tx() as db:_,body=self.service.catalog.intent(db,self.p,run)
        with self.service.native(body) as native:
            delivery=native.queue.poll('worker',capability_tags=['pdf_inspection'])
            native._transition(body['native_job_id'],'READY','RUNNING',input_refs=delivery.task.input_artifact_refs,reason='worker_started')
        self.error(lambda:self.service.control(self.p,run,'cancel',1),'running_or_terminal_control_unavailable')
    def test_pause_survives_restart(self):
        run=self.make_run();self.service.control(self.p,run,'pause',1)
        self.assertEqual(Service(self.root,self.creds).work_once(self.p,run)['outcome'],'PAUSED')
    def test_replay_pause_has_no_duplicate_audit(self):
        run=self.make_run();self.service.control(self.p,run,'pause',1);before=self.service.timeline(self.p,run)
        self.assertTrue(self.service.control(self.p,run,'pause',2)['replayed']);self.assertEqual(before,self.service.timeline(self.p,run))
    def test_no_http_worker_invocation(self):
        self.assertEqual(self.client.post('/operator/v1/worker',headers=self.headers).status_code,404)
    def test_cross_origin_write_rejected(self):
        r=self.client.post('/operator/v1/runs',headers={**self.headers,'Origin':'https://evil.invalid'},json={})
        self.assertEqual(r.status_code,403)
    def test_control_http_rejects_missing_revision(self):self.assertEqual(self.post('runs/'+self.make_run()+'/control',{'action':'cancel'}).status_code,400)
    def test_catalog_lock_prevents_racing_dispatch(self):
        run=self.make_run()
        with self.service.catalog.tx():
            self.error(lambda:self.service.work_once(self.p,run),'storage_busy_or_unavailable')
        self.assertEqual(self.service.status(self.p,run)['status'],'READY')
    def test_native_worker_race_cannot_fake_cancellation(self):
        import threading
        from bie.document_intelligence.real_pdf_toc_runtime import inspect_real_pdf_toc
        run=self.make_run();started=threading.Event();release=threading.Event();out=[]
        def inspect(data):
            started.set();self.assertTrue(release.wait(5));return inspect_real_pdf_toc(data)
        with patch('apps.api.job_service.inspect_real_pdf_toc',side_effect=inspect):
            t=threading.Thread(target=lambda:out.append(self.service.work_once(self.p,run)));t.start()
            try:
                self.assertTrue(started.wait(5))
                self.error(lambda:self.service.control(self.p,run,'cancel',1),'storage_busy_or_unavailable')
            finally:release.set();t.join(10)
        self.assertFalse(t.is_alive());self.assertEqual(out[0]['outcome'],'ACKED')
        self.assertEqual(self.service.status(self.p,run)['status'],'SUCCEEDED')

class Graph001(Base):
    def payload(self):return dict(source_hash=SHA,nodes=[{'id':'a','label':'Concept A'},{'id':'b','label':'Concept B'}],
                                   edges=[{'source':'a','target':'b','type':'related_to'}])
    def publish(self,run,payload=None):return self.service.publish_graph(self.p,run,'concept',payload or self.payload(),evidence_origin='SYNTHETIC_TEST')
    def test_missing_graph_is_not_run(self):self.assertEqual(self.service.graph(self.p,self.make_run(),'concept')['status'],'NOT_RUN')
    def test_persisted_canonical_graph_nodes_relations(self):
        run=self.make_run();g=self.publish(run);self.assertEqual(len(g['graph']['nodes']),2);self.assertEqual(len(g['graph']['edges']),1)
        self.assertEqual(g['evidence_origin'],'SYNTHETIC_TEST');self.assertFalse(g['semantic_correctness_claimed'])
    def test_native_build_and_validate_are_invoked(self):
        import apps.operator.graphs as module
        with patch.object(module,'build',wraps=module.build) as b,patch.object(module,'validate',wraps=module.validate) as v:
            self.publish(self.make_run())
        self.assertGreaterEqual(b.call_count,1);self.assertGreaterEqual(v.call_count,1)
    def test_dangling_edge_rejected(self):
        p=self.payload();p['edges'][0]['target']='unknown'
        self.error(lambda:self.publish(self.make_run(),p),'invalid_graph_edge')
    def test_duplicate_node_rejected(self):
        p=self.payload();p['nodes'].append(p['nodes'][0])
        self.error(lambda:self.publish(self.make_run(),p),'duplicate_graph_node')
    def test_graph_resource_limit(self):
        p=self.payload();p['nodes']=[{'id':'n'+str(i),'label':'node'} for i in range(201)]
        self.error(lambda:self.publish(self.make_run(),p),'graph_limit')
    def test_graph_source_mismatch_rejected(self):
        p=self.payload();p['source_hash']='0'*64
        self.error(lambda:self.publish(self.make_run(),p),'graph_source_mismatch')
    def test_graph_replay_is_immutable(self):
        run=self.make_run();self.publish(run);p=self.payload();p['nodes'][0]['label']='Changed'
        self.error(lambda:self.publish(run,p),'graph_immutable_conflict')
    def test_graph_restored_from_canonical_cas_after_restart(self):
        run=self.make_run();g=self.publish(run)
        self.assertEqual(Service(self.root,self.creds).graph(self.p,run,'concept'),g)
    def test_html_label_is_data_not_dom(self):
        p=self.payload();p['nodes'][0]['label']='<img src=x onerror=alert(1)>'
        self.publish(self.make_run(),p);js=self.client.get('/static/operator.js').text
        self.assertNotIn('innerHTML=',js);self.assertIn('text.textContent=n.label',js)
    def test_graph_ui_svg_and_accessible_fallback(self):
        js=self.client.get('/static/operator.js').text
        self.assertIn("createElementNS(ns,'svg')",js);self.assertIn("document.createElement('table')",js)
    def test_cross_tenant_graph_rejected(self):
        run=self.make_run();self.publish(run);p=Principal('other','tenant-b',PERMISSIONS,time.time()+100)
        self.creds.grant(secrets.token_hex(32),p)
        self.error(lambda:self.service.graph(p,run,'concept'),'run_not_found')

class Graph002(Graph001):
    def payload(self):return dict(source_hash=SHA,nodes=[{'id':'a','label':'Foundation'},{'id':'b','label':'Dependent'}],
                                   edges=[{'source':'a','target':'b','type':'prerequisite'}])
    def publish(self,run,payload=None):return self.service.publish_graph(self.p,run,'prerequisite',payload or self.payload(),evidence_origin='SYNTHETIC_TEST')
    def test_prerequisite_direction_preserved(self):
        g=self.publish(self.make_run())['graph'];self.assertEqual(g['edges'][0]['source'],'a');self.assertEqual(g['edges'][0]['target'],'b')
    def test_native_prerequisite_contract_invoked(self):
        import apps.operator.graphs as module
        with patch.object(module,'build_graph',wraps=module.build_graph) as native:self.publish(self.make_run())
        self.assertGreaterEqual(native.call_count,1)
    def test_cycle_rejected_not_silently_repaired(self):
        p=self.payload();p['edges'].append({'source':'b','target':'a','type':'prerequisite'})
        self.error(lambda:self.publish(self.make_run(),p),'prerequisite_cycle')
    def test_self_loop_rejected(self):
        p=self.payload();p['edges'][0]['target']='a'
        with self.assertRaises(ValueError):self.publish(self.make_run(),p)
    def test_root_and_teaching_order_are_canonical(self):
        g=self.publish(self.make_run())['graph'];self.assertEqual(g['roots'],['a']);self.assertEqual(g['order'],['a','b'])
    def test_deterministic_order_when_input_reversed(self):
        run=self.make_run();p=self.payload();a=self.publish(run,p)
        p['nodes'].reverse();b=self.publish(run,p);self.assertEqual(a['sha256'],b['sha256'])
    def test_wrong_relation_type_rejected(self):
        p=self.payload();p['edges'][0]['type']='related'
        self.error(lambda:self.publish(self.make_run(),p),'invalid_prerequisite_relation')
    def test_missing_prerequisite_not_run(self):self.assertEqual(self.service.graph(self.p,self.make_run(),'prerequisite')['status'],'NOT_RUN')
    def test_view_has_direction_arrows_and_order_fallback(self):
        js=self.client.get('/static/operator.js').text
        self.assertIn('marker-end',js);self.assertIn('Teaching order:',js)
    def test_no_web_graph_publish_endpoint(self):
        self.assertEqual(self.post('runs/'+self.make_run()+'/graphs/prerequisite',self.payload()).status_code,405)

TASK_CLASSES={'BIE-APP-RUN-'+str(n).zfill(3):globals()['Run'+str(n).zfill(3)] for n in range(1,9)}
TASK_CLASSES.update({'BIE-APP-GRAPH-001':Graph001,'BIE-APP-GRAPH-002':Graph002})

def selected_suite(task=None):
    suite=unittest.TestSuite();classes=TASK_CLASSES.values() if task is None else [TASK_CLASSES[task]]
    # Only methods declared by that atomic task: shared helper inheritance is NOT
    # counted as new tests. Each authored method has exactly one canonical ID.
    for cls in classes:
        for name in sorted(n for n in cls.__dict__ if n.startswith('test_')):suite.addTest(cls(name))
    return suite

if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(selected_suite(sys.argv[1] if len(sys.argv)>1 else None))
    raise SystemExit(not result.wasSuccessful())
