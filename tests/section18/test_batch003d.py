"""Actual control-plane contracts plus explicit synthetic fault injections."""
from pathlib import Path
import json,secrets,sqlite3,sys,time,unittest,threading
from dataclasses import replace
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).parent))
from test_batch001 import Base
from apps.operator.service import Service
from apps.operator.contracts import Principal,OperatorError,canonical,digest
from apps.operator.administration import Administration
from bie.model_gateway.provider_registry import ProviderRegistry,ProviderDescriptor
from bie.model_gateway.availability import Health
from bie.infrastructure.worker_health import classify
from bie.infrastructure.worker_scheduler import WorkerCapabilities
from bie.infrastructure.durable_task_queue import SQLiteDurableTaskQueue
from bie.document_intelligence.real_pdf_toc_runtime import RealPdfTocRuntimeError,inspect_real_pdf_toc

class NeverInvokedAdapter:
    """No generated output or claimed provider health; only a registry test port."""
    def invoke(self,request):raise AssertionError('LIVE_PROVIDER_INVOCATION_FORBIDDEN')

class AdminBase(Base):
    def setUp(self):super().setUp();self.admin=self.service.administration
    def provision(self,provider='local-test',model='registry-only',enabled=True,reference=None):
        descriptor=ProviderDescriptor(provider,model,frozenset({'text','structured_output'}),enabled)
        self.config=self.admin.provision_provider(self.p,descriptor,NeverInvokedAdapter(),
                          secret_reference=reference,evidence_origin='SYNTHETIC_TEST')
        return self.config
    def provider(self):return self.admin.providers(self.p)['items'][0]
    def failed(self,key='failed'):
        run=self.make_run(key)
        with patch('apps.api.job_service.inspect_real_pdf_toc',side_effect=RealPdfTocRuntimeError('PRIVATE_SOURCE')):
            self.service.work_once(self.p,run)
        return run
    def deny(self,permissions):
        p=Principal('limited','tenant-a',frozenset(permissions),time.time()+100)
        token=secrets.token_hex(32);self.creds.grant(token,p);return p,{'Authorization':'Bearer '+token}
    def recovery(self,run,key='recover'):
        d=self.admin.dead_letter(self.p,run)
        return dict(idempotency_key=key,expected_revision=d['parent_revision'],expected_queue_digest=d['queue']['queue_digest'])

class Admin001(AdminBase):
    def test_empty_registry_truthful_not_configured(self):
        r=self.get('admin/providers');self.assertEqual(r.status_code,200);self.assertEqual(r.json()['status'],'NOT_CONFIGURED')
    def test_canonical_registry_register_really_invoked(self):
        calls=[];original=ProviderRegistry.register
        def spy(registry,d,a):calls.append(d);return original(registry,d,a)
        with patch.object(ProviderRegistry,'register',spy):self.provision();r=self.provider()
        self.assertGreaterEqual(len(calls),2);self.assertTrue(r['bound_in_this_process']);self.assertEqual(r['health_status'],'NOT_RUN')
    def test_canonical_candidates_reflect_disabled_config(self):
        self.provision();self.assertEqual(len(self.admin.runtime_registry(self.p).candidates({'text'})),1)
        self.admin.set_provider_enabled(self.p,self.config,False,1,'disable')
        self.assertEqual(self.admin.runtime_registry(self.p).candidates({'text'}),())
    def test_configuration_survives_restart_binding_does_not(self):
        self.provision();a=Service(self.root,self.creds).administration.providers(self.p)['items'][0]
        self.assertEqual(a['config_id'],self.config);self.assertFalse(a['bound_in_this_process'])
        self.assertEqual(a['health_reason'],'adapter_not_bound_in_this_process')
    def test_restart_cannot_enable_unbound_provider(self):
        self.provision();a=Service(self.root,self.creds).administration
        self.error(lambda:a.set_provider_enabled(self.p,self.config,True,1,'enable'),'provider_adapter_not_bound')
    def test_trusted_rebinding_restores_actual_registry(self):
        self.provision();a=Service(self.root,self.creds).administration
        d=ProviderDescriptor('local-test','registry-only',frozenset({'text','structured_output'}))
        a.bind_provider(self.p,self.config,d,NeverInvokedAdapter())
        self.assertEqual(len(a.runtime_registry(self.p).candidates({'text'})),1)
    def test_rebinding_cannot_expand_capabilities(self):
        self.provision();d=ProviderDescriptor('local-test','registry-only',frozenset({'vision'}))
        self.error(lambda:self.admin.bind_provider(self.p,self.config,d,NeverInvokedAdapter()),'provider_binding_mismatch')
    def test_secret_reference_opaque_only(self):
        self.provision(reference='secretref-'+'a'*64)
        result=json.dumps(self.admin.providers(self.p));self.assertIn('secretref-',result)
        self.assertFalse(self.provider()['secret_values_exposed']);self.assertNotIn('api_key',result)
    def test_raw_secret_reference_rejected(self):
        self.error(lambda:self.provision(reference='RAW-CREDENTIAL-DO-NOT-PERSIST'),'secret_reference_invalid')
        self.assertEqual(self.admin.providers(self.p)['items'],[])
    def test_unknown_capability_rejected(self):
        d=ProviderDescriptor('local','test',frozenset({'invented'}))
        self.error(lambda:self.admin.provision_provider(self.p,d,NeverInvokedAdapter(),evidence_origin='SYNTHETIC_TEST'),
                   'provider_capabilities_invalid')
    def test_health_is_only_a_bound_observation(self):
        self.provision();r=self.provider();h=Health(r['provider_id'],r['model_id'],True,12,time.time())
        self.admin.observe_provider_health(self.p,self.config,h,configuration_sha256=r['configuration_sha256'],evidence_origin='SYNTHETIC_TEST')
        r=self.provider();self.assertEqual(r['health_status'],'AVAILABLE');self.assertEqual(r['health_origin'],'SYNTHETIC_TEST')
        self.assertFalse(r['live_probe_performed'])
    def test_stale_health_not_available(self):
        self.provision();r=self.provider();h=Health('local-test','registry-only',True,12,time.time()-61)
        self.admin.observe_provider_health(self.p,self.config,h,configuration_sha256=r['configuration_sha256'],evidence_origin='SYNTHETIC_TEST')
        self.assertEqual(self.provider()['health_status'],'STALE');self.assertFalse(self.provider()['health_available'])
    def test_future_or_nan_health_rejected(self):
        self.provision();sha=self.provider()['configuration_sha256']
        for h in (Health('local-test','registry-only',True,float('nan'),time.time()),Health('local-test','registry-only',True,1,time.time()+100)):
            with self.assertRaises(OperatorError):self.admin.observe_provider_health(self.p,self.config,h,configuration_sha256=sha,evidence_origin='SYNTHETIC_TEST')
    def test_health_origin_cannot_promote_test_provider(self):
        self.provision();r=self.provider();h=Health('local-test','registry-only',True,12,time.time())
        self.error(lambda:self.admin.observe_provider_health(self.p,self.config,h,configuration_sha256=r['configuration_sha256'],evidence_origin='NATIVE_OBSERVATION'),'admin_origin_promotion')
    def test_immutable_versions_and_idempotent_replay(self):
        self.provision();a=self.admin.set_provider_enabled(self.p,self.config,False,1,'disable')
        b=self.admin.set_provider_enabled(self.p,self.config,False,1,'disable')
        self.assertTrue(b['replayed']);self.assertEqual(a['configuration_sha256'],b['configuration_sha256'])
        h=self.admin.provider_history(self.p,self.config)['items'];self.assertEqual(len(h),2)
        self.assertTrue(h[0]['configuration']['enabled']);self.assertFalse(h[1]['configuration']['enabled'])
    def test_conflicting_idempotency_and_stale_revision_rejected(self):
        self.provision();self.admin.set_provider_enabled(self.p,self.config,False,1,'key')
        self.error(lambda:self.admin.set_provider_enabled(self.p,self.config,True,1,'key'),'idempotency_conflict')
        self.error(lambda:self.admin.set_provider_enabled(self.p,self.config,True,1,'other'),'stale_revision')
    def test_config_permission_and_tenant_isolation(self):
        self.provision();p,h=self.deny({'read','admin_read'})
        self.assertEqual(self.client.post('/operator/v1/admin/providers/'+self.config+'/enabled',headers=h,
                         json=dict(enabled=False,expected_revision=1,idempotency_key='x')).status_code,403)
        foreign=Principal('foreign','tenant-b',self.p.permissions,time.time()+100);self.creds.grant(secrets.token_hex(32),foreign)
        self.assertEqual(self.admin.providers(foreign)['items'],[])
    def test_http_update_rejects_secret_or_boolean_revision(self):
        self.provision();path='admin/providers/'+self.config+'/enabled'
        self.assertEqual(self.post(path,dict(enabled=False,expected_revision=True,idempotency_key='x')).status_code,400)
        self.assertEqual(self.post(path,dict(enabled=False,expected_revision=1,idempotency_key='x',api_key='PRIVATE')).status_code,400)
    def test_config_catalog_tamper_detected(self):
        self.provision()
        with sqlite3.connect(self.service.catalog.path) as db:db.execute('DELETE FROM provider_versions')
        self.error(lambda:self.admin.providers(self.p),'catalog_state_tampered')
    def test_provider_pagination_and_no_http_adapter_loader(self):
        self.provision(model='one');self.provision(model='two');a=self.admin.providers(self.p,limit=1)
        b=self.admin.providers(self.p,a['next_after'],1);self.assertNotEqual(a['items'][0]['config_id'],b['items'][0]['config_id'])
        self.assertEqual(self.post('admin/providers',{'adapter':'untrusted.module'}).status_code,405)
    def test_revision_ceiling_does_not_create_unpageable_version(self):
        self.provision()
        with self.service.catalog.tx() as db:
            body=self.admin._provider(db,self.p,self.config)
            for n in range(2,257):
                seeded=dict(body,revision=n)
                db.execute('INSERT INTO provider_versions VALUES(?,?,?,?)',(self.p.tenant,self.config,n,canonical(seeded).decode()))
            self.service.catalog.event(db,self.p.actor,'SYNTHETIC_BOUNDARY_INVENTORY',self.config)
        with self.assertRaises(OperatorError) as ctx:self.admin.set_provider_enabled(self.p,self.config,False,256,'limit')
        self.assertEqual(ctx.exception.code,'provider_version_limit');self.assertEqual(ctx.exception.status,429)

class Admin002(AdminBase):
    def test_empty_pool_not_run(self):self.assertEqual(self.admin.workers(self.p)['status'],'NOT_RUN')
    def test_actual_worker_records_canonical_success_and_stop(self):
        run=self.make_run();self.service.work_once(self.p,run);r=self.admin.workers(self.p)['items'][0]
        self.assertEqual(r['outcome'],'ACKED');self.assertEqual(r['lifecycle'],'STOPPED');self.assertEqual(r['queue_state'],'ACKED')
        self.assertEqual(r['active_tasks'],0);self.assertEqual(r['current_workload'],[])
    def test_native_worker_contracts_really_invoked(self):
        run=self.make_run();self.service.work_once(self.p,run)
        with patch('apps.operator.administration.worker_health',wraps=classify) as h,patch.object(WorkerCapabilities,'validate',autospec=True,side_effect=WorkerCapabilities.validate) as c:
            self.admin.workers(self.p)
        self.assertEqual(h.call_count,1);self.assertEqual(c.call_count,1)
    def test_restart_retains_worker_history(self):
        self.service.work_once(self.p,self.make_run());a=self.admin.workers(self.p)
        b=Service(self.root,self.creds).administration.workers(self.p);self.assertEqual(a,b)
    def test_inflight_pool_uses_actual_canonical_lease(self):
        run=self.make_run();started=threading.Event();release=threading.Event();out=[]
        def held(data):started.set();self.assertTrue(release.wait(10));return inspect_real_pdf_toc(data)
        with patch('apps.api.job_service.inspect_real_pdf_toc',side_effect=held):
            thread=threading.Thread(target=lambda:out.append(self.service.work_once(self.p,run)));thread.start()
            try:
                self.assertTrue(started.wait(5));w=self.admin.workers(self.p)['items'][0]
                self.assertEqual(w['queue_state'],'DELIVERED');self.assertEqual(len(w['current_workload']),1)
                self.assertEqual(w['lease_status'],'ACTIVE')
            finally:release.set();thread.join(15)
        self.assertFalse(thread.is_alive());self.assertEqual(out[0]['outcome'],'ACKED')
    def test_stale_heartbeat_not_claimed_dead(self):
        run=self.make_run();worker=self.admin.begin_worker(self.p,run)
        with patch('apps.operator.administration.time.time',return_value=time.time()+61):w=self.admin.workers(self.p)['items'][0]
        self.assertEqual(w['health'],'STALE');self.assertEqual(w['liveness'],'UNVERIFIED_STALE');self.assertFalse(w['death_inferred_from_stale'])
        self.admin.finish_worker(self.p,worker,'INTERRUPTED')
    def test_worker_failure_is_actual_safe_terminal_outcome(self):
        self.failed();w=self.admin.workers(self.p)['items'][0]
        self.assertEqual(w['outcome'],'FAILED');self.assertEqual(w['health'],'DEGRADED');self.assertNotIn('PRIVATE',json.dumps(w))
    def test_paused_dispatch_does_not_fabricate_active_work(self):
        run=self.make_run();self.service.control(self.p,run,'pause',1);self.service.work_once(self.p,run)
        w=self.admin.workers(self.p)['items'][0];self.assertEqual(w['outcome'],'PAUSED');self.assertEqual(w['current_workload'],[])
    def test_interruption_record_not_fake_failed_engine(self):
        run=self.make_run()
        with patch.object(self.service,'_execute_once',side_effect=RuntimeError('PRIVATE_WORKER_PATH')):
            with self.assertRaises(RuntimeError):self.service.work_once(self.p,run)
        w=self.admin.workers(self.p)['items'][0];self.assertEqual(w['outcome'],'INTERRUPTED')
        self.assertEqual(self.service.status(self.p,run)['status'],'READY')
    def test_worker_permission_fail_closed(self):
        p,h=self.deny({'read'});self.error(lambda:self.service.work_once(p,self.make_run()),'forbidden')
        self.assertEqual(self.client.get('/operator/v1/admin/workers',headers=h).status_code,403)
    def test_worker_foreign_tenant_invisible(self):
        self.service.work_once(self.p,self.make_run());p=Principal('foreign','tenant-b',self.p.permissions,time.time()+100)
        self.creds.grant(secrets.token_hex(32),p);self.assertEqual(self.admin.workers(p)['items'],[])
    def test_worker_record_tamper_detected(self):
        self.service.work_once(self.p,self.make_run())
        with sqlite3.connect(self.service.catalog.path) as db:db.execute('DELETE FROM workers')
        self.error(lambda:self.admin.workers(self.p),'catalog_state_tampered')
    def test_worker_pagination_and_no_http_control(self):
        self.service.work_once(self.p,self.make_run('one'));self.service.work_once(self.p,self.make_run('two'))
        a=self.admin.workers(self.p,limit=1);b=self.admin.workers(self.p,a['next_after'],1)
        self.assertNotEqual(a['items'][0]['worker_id'],b['items'][0]['worker_id'])
        self.assertEqual(self.post('admin/workers',{'action':'start'}).status_code,405)

class Admin003(AdminBase):
    def test_queue_native_ready_and_hash_link(self):
        run=self.make_run();q=self.admin.queue(self.p)['items'][0]
        self.assertEqual(q['run_id'],run);self.assertEqual(q['state'],'READY');self.assertEqual(len(q['source_hash']),64)
        self.assertNotIn('idempotency_key',q)
    def test_queue_get_does_not_recover_expired_or_poll(self):
        self.make_run()
        with patch.object(SQLiteDurableTaskQueue,'recover_expired',side_effect=AssertionError('MUTATING_READ')),patch.object(SQLiteDurableTaskQueue,'poll',side_effect=AssertionError('MUTATING_READ')):
            self.assertEqual(self.get('admin/queue').status_code,200)
    def test_queue_ack_state_after_actual_work(self):
        self.service.work_once(self.p,self.make_run());q=self.admin.queue(self.p,state='ACKED')['items'][0]
        self.assertEqual(q['delivery_count'],1);self.assertIsNotNone(q['acked_at'])
    def test_state_filter_truthful_empty(self):
        self.make_run();self.assertEqual(self.admin.queue(self.p,state='DEAD_LETTER')['status'],'EMPTY')
    def test_unknown_filter_invalid_pagination_rejected(self):
        for kwargs in ({'state':'SUCCEEDED'},{'limit':0},{'limit':True},{'after':'../path'}):
            with self.assertRaises(OperatorError):self.admin.queue(self.p,**kwargs)
    def test_queue_pagination_does_not_repeat_or_leak(self):
        self.make_run('one');self.make_run('two');a=self.admin.queue(self.p,limit=1);b=self.admin.queue(self.p,a['next_after'],1)
        self.assertNotEqual(a['items'][0]['run_id'],b['items'][0]['run_id']);self.assertIsNone(b['next_after'])
    def test_queue_foreign_tenant_isolation(self):
        self.make_run();p=Principal('foreign','tenant-b',self.p.permissions,time.time()+100);self.creds.grant(secrets.token_hex(32),p)
        self.assertEqual(self.admin.queue(p)['items'],[])
    def test_queue_cannot_be_read_without_admin_role(self):
        p,h=self.deny({'read'});self.assertEqual(self.client.get('/operator/v1/admin/queue',headers=h).status_code,403)
    def test_revoked_access_rejected(self):
        self.make_run();self.creds.revoke(self.token);self.assertEqual(self.get('admin/queue').status_code,401)
    def test_queue_identity_corruption_not_fake_inventory(self):
        run=self.make_run()
        with sqlite3.connect(self.root/'runs'/run/'queue.sqlite3') as db:db.execute("UPDATE queue_tasks SET capability_tags_json='[\"invented\"]'")
        self.error(lambda:self.admin.queue(self.p),'queue_identity_invalid')
    def test_queue_unknown_reason_is_hashed_not_echoed(self):
        run=self.make_run()
        with sqlite3.connect(self.root/'runs'/run/'queue.sqlite3') as db:db.execute('UPDATE queue_tasks SET last_reason=?',('SECRET C:/user/path',))
        q=self.admin.queue(self.p)['items'][0];self.assertEqual(q['reason_code'],'diagnostic_redacted')
        self.assertEqual(len(q['reason_sha256']),64);self.assertNotIn('SECRET',json.dumps(q))
    def test_queue_digest_is_repeatable(self):
        self.make_run();self.assertEqual(self.admin.queue(self.p),self.admin.queue(self.p))
    def test_no_http_queue_mutation_endpoint(self):self.assertEqual(self.post('admin/queue',{'state':'ACKED'}).status_code,405)
    def test_queue_delivery_counter_tamper_rejected(self):
        run=self.make_run()
        with sqlite3.connect(self.root/'runs'/run/'queue.sqlite3') as db:db.execute('UPDATE queue_tasks SET delivery_count=2')
        self.error(lambda:self.admin.queue(self.p),'queue_delivery_count_invalid')
    def test_ack_without_ack_timestamp_rejected(self):
        run=self.make_run();self.service.work_once(self.p,run)
        with sqlite3.connect(self.root/'runs'/run/'queue.sqlite3') as db:db.execute('UPDATE queue_tasks SET acked_at=NULL')
        self.error(lambda:self.admin.queue(self.p),'queue_transition_invalid')

class Admin004(AdminBase):
    def test_actual_dead_letter_native_failure_and_events(self):
        run=self.failed();d=self.admin.dead_letter(self.p,run)
        self.assertEqual(d['engine_state'],'FAILED');self.assertEqual(d['queue']['state'],'DEAD_LETTER')
        self.assertEqual([e['event_type'] for e in d['events']],['ENQUEUED','DELIVERED','DEAD_LETTERED'])
    def test_non_dead_letter_rejected(self):self.error(lambda:self.admin.dead_letter(self.p,self.make_run()),'not_dead_letter')
    def test_recovery_preserves_parent_and_creates_child(self):
        run=self.failed();before=self.service.timeline(self.p,run);r=self.post('admin/dead-letters/'+run+'/retry',self.recovery(run))
        self.assertEqual(r.status_code,202);child=r.json()['run_id'];self.assertNotEqual(child,run)
        self.assertEqual(self.service.status(self.p,child)['status'],'READY');self.assertEqual(self.service.timeline(self.p,run),before)
        self.assertEqual(self.service.status(self.p,run)['queue_state'],'DEAD_LETTER')
    def test_replay_same_child_no_duplicate_queue_work(self):
        run=self.failed();request=self.recovery(run);a=self.post('admin/dead-letters/'+run+'/retry',request).json()
        b=self.post('admin/dead-letters/'+run+'/retry',request).json();self.assertEqual(a['run_id'],b['run_id']);self.assertTrue(b['replayed'])
        self.assertEqual(len(self.service.list_runs(self.p)['items']),2)
    def test_recovered_child_executes_actual_runtime(self):
        run=self.failed();child=self.post('admin/dead-letters/'+run+'/retry',self.recovery(run)).json()['run_id']
        self.assertEqual(self.service.work_once(self.p,child)['outcome'],'ACKED')
        self.assertEqual(self.service.status(self.p,child)['status'],'SUCCEEDED');self.assertEqual(self.service.status(self.p,run)['status'],'FAILED')
    def test_completed_child_replay_not_falsely_ready(self):
        run=self.failed();request=self.recovery(run);path='admin/dead-letters/'+run+'/retry'
        child=self.post(path,request).json()['run_id'];self.service.work_once(self.p,child)
        replay=self.post(path,request).json();self.assertTrue(replay['replayed'])
        self.assertEqual(replay['child_status'],'SUCCEEDED');self.assertEqual(replay['child_queue_state'],'ACKED')
    def test_recovery_never_calls_unsafe_native_redrive(self):
        run=self.failed()
        with patch.object(SQLiteDurableTaskQueue,'redrive',side_effect=AssertionError('UNSAFE_REDRIVE')):
            self.assertEqual(self.post('admin/dead-letters/'+run+'/retry',self.recovery(run)).status_code,202)
    def test_cancelled_parent_requires_review_not_retry(self):
        run=self.make_run();self.service.control(self.p,run,'cancel',1);d=self.admin.dead_letter(self.p,run)
        self.assertFalse(d['can_recover']);self.assertEqual(d['recovery_action'],'REVIEW_REQUIRED')
        self.assertEqual(self.post('admin/dead-letters/'+run+'/retry',self.recovery(run)).status_code,409)
    def test_stale_queue_or_revision_cannot_spawn_child(self):
        run=self.failed();request=self.recovery(run)
        for field,value in (('expected_revision',2),('expected_queue_digest','0'*64)):
            self.assertEqual(self.post('admin/dead-letters/'+run+'/retry',dict(request,**{field:value})).status_code,409)
        self.assertEqual(len(self.service.list_runs(self.p)['items']),1)
    def test_recovery_permission_and_tenant_isolation(self):
        run=self.failed();p,h=self.deny({'read','admin_read','retry','create'})
        self.assertEqual(self.client.post('/operator/v1/admin/dead-letters/'+run+'/retry',headers=h,json=self.recovery(run)).status_code,403)
        p=Principal('foreign','tenant-b',self.p.permissions,time.time()+100);self.creds.grant(secrets.token_hex(32),p)
        self.error(lambda:self.admin.dead_letter(p,run),'run_not_found')
    def test_event_reason_secret_redacted(self):
        run=self.failed()
        with sqlite3.connect(self.root/'runs'/run/'queue.sqlite3') as db:db.execute('UPDATE queue_events SET reason=?',('PRIVATE_STACK_SECRET',))
        d=self.admin.dead_letter(self.p,run);self.assertNotIn('PRIVATE_STACK_SECRET',json.dumps(d))
        self.assertTrue(all(e['reason_code']=='diagnostic_redacted' for e in d['events']))
    def test_event_pagination_order(self):
        run=self.failed();a=self.admin.dead_letter(self.p,run,limit=1);b=self.admin.dead_letter(self.p,run,a['next_sequence'],1)
        self.assertGreater(b['events'][0]['sequence'],a['events'][0]['sequence'])
    def test_recovery_audit_exactly_once_and_parent_lineage(self):
        run=self.failed();request=self.recovery(run);self.post('admin/dead-letters/'+run+'/retry',request);self.post('admin/dead-letters/'+run+'/retry',request)
        with self.service.catalog.tx(read_only=True) as db:
            rows=[json.loads(r[0]) for r in db.execute('SELECT body FROM audit')]
        records=[r for r in rows if r['action']=='DEAD_LETTER_CHILD_CREATED'];self.assertEqual(len(records),1)
        self.assertEqual(records[0]['details']['parent_run_id'],run)
    def test_parent_rechecked_inside_native_create_transaction(self):
        run=self.failed();request=self.recovery(run);original=self.service.retry
        def moved(p,id,key,**kwargs):
            with sqlite3.connect(self.root/'runs'/run/'queue.sqlite3') as db:db.execute("UPDATE queue_tasks SET last_reason='manual redrive'")
            return original(p,id,key,**kwargs)
        with patch.object(self.service,'retry',side_effect=moved):r=self.post('admin/dead-letters/'+run+'/retry',request)
        self.assertEqual(r.status_code,409);self.assertEqual(r.json()['error']['code'],'stale_dead_letter_state')
    def test_invalid_recovery_body_rejected(self):
        run=self.failed();request=self.recovery(run)
        self.assertEqual(self.post('admin/dead-letters/'+run+'/retry',dict(request,force=True)).status_code,400)
    def test_restart_keeps_failure_and_child_recovery(self):
        run=self.failed();a=self.admin.dead_letter(self.p,run);new=Service(self.root,self.creds)
        self.assertEqual(new.administration.dead_letter(self.p,run),a)
        self.assertEqual(new.administration.recover_dead_letter(self.p,run,'retry',a['parent_revision'],a['queue']['queue_digest'])['parent_state'],'FAILED')

TASK_CLASSES={'BIE-APP-ADMIN-001':Admin001,'BIE-APP-ADMIN-002':Admin002,'BIE-APP-ADMIN-003':Admin003,'BIE-APP-ADMIN-004':Admin004}
def selected_suite(task=None):
    suite=unittest.TestSuite()
    for key,cls in TASK_CLASSES.items():
        if task is None or task==key:
            for name in sorted(cls.__dict__):
                if name.startswith('test_'):suite.addTest(cls(name))
    return suite
if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(selected_suite());raise SystemExit(not result.wasSuccessful())
