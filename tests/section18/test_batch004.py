"""Versioning, actual canonical consumers, access isolation and seeded negatives."""
from pathlib import Path
import copy,json,secrets,sqlite3,sys,time,unittest
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).parent))
from test_batch001 import Base,DATA
from quality_fixtures import release_inputs
from apps.operator.service import Service
from apps.operator.contracts import Principal,PERMISSIONS,canonical,digest,OperatorError
from apps.operator.governance import Governance,validate_policy,validate_benchmark
from bie.infrastructure.policy_inheritance import policy_chain
from bie.infrastructure.run_config import RunConfig
from bie.infrastructure.audit_log import AuditLog
from bie.evaluation.benchmarks.release.ledger import ReleaseLedger
from bie.evaluation.benchmarks.release import gate,aggregation
from bie.evaluation.benchmarks.models import BenchmarkError

class GovernanceBase(Base):
    def setUp(self):super().setUp();self.g=self.service.governance
    def policy(self,locale='en',limit=None):return dict(model_policy='offline_only',locale=locale,deterministic=True,
        limits={'pdf_bytes':self.service.limit if limit is None else limit})
    def save(self,c=None,revision=0,key='save',id='policy-one',kind='policy'):
        return self.g.save(self.p,kind,id,self.policy() if c is None else c,revision,key)
    def activate(self,r,key='activate',previous=None):
        return self.g.activate(self.p,r['kind'],r['config_id'],r['revision'],r['configuration_sha256'],previous,key)
    def bound(self,r,key='bound',source=None):
        return self.service.create(self.p,source or self.source()['source_id'],{'locale':r['configuration']['locale']},key,
            policy_binding=dict(config_id=r['config_id'],revision=r['revision'],configuration_sha256=r['configuration_sha256']))
    def body(self,run):
        with self.service.catalog.tx(read_only=True) as db:return self.service.catalog.intent(db,self.p,run)[1]
    def benchmark(self,production=False):
        run=self.make_run();m,p,a=release_inputs(self.body(run),production);return dict(manifest=m,policy=p),a
    def foreign(self):
        p=Principal('other','tenant-b',PERMISSIONS,time.time()+1000);self.creds.grant(secrets.token_hex(32),p);return p
    def reader(self):
        p=Principal('reader','tenant-a',frozenset({'read','admin_read'}),time.time()+1000)
        t=secrets.token_hex(32);self.creds.grant(t,p);return p,{'Authorization':'Bearer '+t}

class Admin005(GovernanceBase):
    def test_empty_is_not_configured_not_engine_success(self):
        v=self.g.list(self.p,'policy');self.assertEqual(v['status'],'NOT_CONFIGURED');self.assertEqual(v['execution_status'],'NOT_RUN')
    def test_canonical_inheritance_really_used(self):
        with patch('apps.operator.governance.policy_chain',wraps=policy_chain) as native:self.save()
        self.assertEqual(native.call_count,1)
    def test_versions_are_immutable_and_diff_is_exact(self):
        a=self.save();b=self.save(self.policy('hi'),1,'second')
        self.assertEqual(a['configuration']['locale'],'en');self.assertEqual(b['previous_sha256'],a['configuration_sha256'])
        self.assertEqual(self.g.diff(self.p,'policy','policy-one',1,2)['changes'],[dict(path='/locale',before='en',after='hi')])
    def test_save_replay_without_new_version_or_event(self):
        a=self.save();b=self.save();self.assertTrue(b['replayed']);self.assertEqual(a['configuration_sha256'],b['configuration_sha256'])
        self.assertEqual(len(self.g.history(self.p,'policy','policy-one')['items']),1)
        self.assertEqual(len(self.g.audit(self.p)['items']),1)
    def test_same_key_changed_payload_conflicts(self):
        self.save();self.error(lambda:self.save(self.policy('hi')),'idempotency_conflict')
    def test_stale_revision_rejected(self):
        self.save();self.error(lambda:self.save(key='new'),'stale_configuration_revision')
    def test_activate_explicit_pins_and_compare_and_set(self):
        a=self.save();v=self.activate(a);b=self.save(self.policy('hi'),1,'second')
        self.error(lambda:self.activate(b,key='changed'),'stale_activation')
        w=self.activate(b,key='changed',previous=v['active']['activation_sha256']);self.assertEqual(w['active']['revision'],2)
    def test_old_activation_replay_cannot_revert_current(self):
        a=self.save();v=self.activate(a);b=self.save(self.policy('hi'),1,'second')
        w=self.activate(b,'second-active',v['active']['activation_sha256']);r=self.activate(a)
        self.assertTrue(r['replayed']);self.assertFalse(r['requested_is_active']);self.assertEqual(r['active'],w['active'])
    def test_canonical_runconfig_consumes_bound_policy(self):
        r=self.save(self.policy('hi'));self.activate(r)
        with patch.object(RunConfig,'validate',autospec=True,side_effect=RunConfig.validate) as native:v=self.bound(r)
        self.assertGreaterEqual(native.call_count,1);b=self.body(v['run_id'])
        self.assertEqual(b['config']['locale'],'hi');self.assertEqual(b['config']['metadata']['policy_sha256'],r['configuration_sha256'])
        self.assertEqual(self.service.work_once(self.p,v['run_id'])['outcome'],'ACKED')
    def test_old_run_config_survives_activation_and_replay(self):
        a=self.save();self.activate(a);run=self.bound(a);before=self.body(run['run_id']);b=self.save(self.policy('hi'),1,'next')
        active=self.g.list(self.p,'policy')['active'];self.activate(b,'next-active',active['activation_sha256'])
        self.assertEqual(self.bound(a)['run_id'],run['run_id']);self.assertEqual(self.body(run['run_id']),before)
        self.error(lambda:self.bound(a,'new'),'policy_not_active')
    def test_policy_real_source_limit_blocks_new_run(self):
        r=self.save(self.policy(limit=len(DATA)-1));self.activate(r)
        self.error(lambda:self.bound(r),'policy_source_too_large');self.assertEqual(self.service.list_runs(self.p)['items'],[])
    def test_unbound_or_unknown_policy_never_enables_live_engine(self):
        for v in (dict(self.policy(),model_policy='quality_first'),dict(self.policy(),feature_flags={'fake':True}),dict(self.policy(),deterministic=False)):
            with self.assertRaises(OperatorError):self.save(v)
    def test_boundary_bool_and_oversize_limit_rejected(self):
        for limit in (True,0,self.service.limit+1):
            with self.assertRaises(OperatorError):self.save(self.policy(limit=limit))
        with self.assertRaises(OperatorError):self.save(revision=True)
    def test_policy_binding_wrong_hash_and_locale_fail_closed(self):
        r=self.save();self.activate(r);bad=dict(r,configuration_sha256='0'*64)
        self.error(lambda:self.bound(bad),'policy_not_active')
        wrong=copy.deepcopy(r);wrong['configuration']['locale']='hi';self.error(lambda:self.bound(wrong),'policy_options_conflict')
    def test_restart_retains_versions_and_activation(self):
        r=self.save();self.activate(r);other=Service(self.root,self.creds)
        self.assertEqual(other.governance.list(self.p,'policy'),self.g.list(self.p,'policy'))
    def test_tenant_isolated_identical_ids_and_404_history(self):
        self.save();p=self.foreign();self.assertEqual(self.g.list(p,'policy')['items'],[])
        self.error(lambda:self.g.history(p,'policy','policy-one'),'configuration_not_found')
        self.g.save(p,'policy','policy-one',self.policy('hi'),0,'same-key');self.assertEqual(self.g.list(self.p,'policy')['items'][0]['configuration']['locale'],'en')
    def test_unauthorized_update_logged_without_payload(self):
        p,h=self.reader();r=self.client.post('/operator/v1/governance/policy/policy-one/versions',headers=h,
            json=dict(configuration=self.policy(),expected_revision=0,idempotency_key='private-key'))
        self.assertEqual(r.status_code,403);audit=self.g.audit(self.p)['items'];self.assertEqual(audit[0]['authorization'],'DENY')
        self.assertNotIn('private-key',json.dumps(audit))
    def test_tamper_version_or_activation_detected(self):
        r=self.save();self.activate(r)
        with sqlite3.connect(self.service.catalog.path) as db:db.execute('DELETE FROM governance_active')
        self.error(lambda:self.g.list(self.p,'policy'),'catalog_state_tampered')
    def test_pagination_and_version_ceiling(self):
        r=self.save();self.save(self.policy('hi'),1,'next')
        a=self.g.history(self.p,'policy','policy-one',limit=1);b=self.g.history(self.p,'policy','policy-one',a['next_revision'],1)
        self.assertEqual(b['items'][0]['revision'],2)
        with patch('apps.operator.governance.MAX_VERSIONS',2):self.error(lambda:self.save(self.policy(),2,'third'),'configuration_version_limit')
    def test_concurrent_version_writers_one_wins_no_loss(self):
        with ThreadPoolExecutor(max_workers=2) as pool:
            def attempt(n):
                try:return self.save(self.policy('hi' if n else 'en'),key='writer-'+str(n))['revision']
                except OperatorError as e:return e.code
            values=list(pool.map(attempt,range(2)))
        self.assertEqual(sorted(map(str,values)),['1','stale_configuration_revision']);self.assertEqual(len(self.g.history(self.p,'policy','policy-one')['items']),1)
    def test_http_rejects_unknown_fields_and_no_policy_execution_route(self):
        r=self.post('governance/policy/id/versions',dict(configuration=self.policy(),expected_revision=0,idempotency_key='x',force=True))
        self.assertEqual(r.status_code,400);self.assertEqual(self.post('governance/policy/id/execute',{}).status_code,404)
    def test_bound_retry_preserves_canonical_policy_lineage(self):
        from bie.document_intelligence.real_pdf_toc_runtime import RealPdfTocRuntimeError
        r=self.save();self.activate(r);parent=self.bound(r)['run_id']
        with patch('apps.api.job_service.inspect_real_pdf_toc',side_effect=RealPdfTocRuntimeError('seeded_failure')):self.service.work_once(self.p,parent)
        child=self.service.retry(self.p,parent,'retry')['run_id'];body=self.body(child)
        self.assertEqual(body['config']['metadata']['policy_sha256'],r['configuration_sha256']);self.assertEqual(body['parent_run_id'],parent)
        self.assertEqual(self.service.status(self.p,parent)['status'],'FAILED')

class Admin006(GovernanceBase):
    def save_benchmark(self):
        c,a=self.benchmark();return self.save(c,id='benchmark-one',kind='benchmark'),a
    def test_benchmark_native_policy_validation_invoked(self):
        with patch.object(gate,'validate_policy',wraps=gate.validate_policy) as v,patch.object(aggregation,'aggregate',wraps=aggregation.aggregate) as a:self.save_benchmark()
        self.assertGreaterEqual(v.call_count,1);self.assertGreaterEqual(a.call_count,1)
    def test_frozen_dataset_metrics_raters_and_floors_present(self):
        r,a=self.save_benchmark();c=self.g.list(self.p,'benchmark')['items'][0]['configuration']
        self.assertEqual(c['manifest']['dataset_sha256'],r['configuration']['manifest']['dataset_sha256'])
        self.assertEqual(len(c['policy']['aggregation']['raters']),2);self.assertTrue(c['policy']['critical_floors']['floors'])
    def test_missing_measurements_actual_ledger_is_blocked(self):
        r,a=self.save_benchmark();self.activate(r)
        with ReleaseLedger(self.root/'evaluation.sqlite3') as ledger:
            receipt=self.g.execute_benchmark(self.p,r['config_id'],1,r['configuration_sha256'],ledger,'campaign','attempt',[],now=1000)
        self.assertEqual(receipt['report']['outcome'],'BLOCKED');self.assertIn('MISSING_REQUIRED_RATER',receipt['report']['reasons'])
        self.assertFalse(receipt['report']['release_authorized']);self.assertFalse(receipt['report']['product_accepted'])
    def test_canonical_ledger_execute_actually_invoked(self):
        r,a=self.save_benchmark();self.activate(r)
        original=ReleaseLedger.execute
        with ReleaseLedger(self.root/'evaluation.sqlite3') as ledger,patch.object(ReleaseLedger,'execute',autospec=True,side_effect=original) as native:
            result=self.g.execute_benchmark(self.p,r['config_id'],1,r['configuration_sha256'],ledger,'campaign','attempt',a,now=1000)
        self.assertEqual(native.call_count,1);self.assertEqual(result['report']['outcome'],'DIAGNOSTIC_PASS')
    def test_candidate_inputs_immutable_after_receipt(self):
        r,a=self.save_benchmark();self.activate(r)
        with ReleaseLedger(self.root/'evaluation.sqlite3') as ledger:
            original=self.g.execute_benchmark(self.p,r['config_id'],1,r['configuration_sha256'],ledger,'campaign','attempt',a)
            c=copy.deepcopy(r['configuration']);c['policy']['enterprise']['minimum_score']='1'
            b=self.save(c,1,'new',id='benchmark-one',kind='benchmark');active=self.g.list(self.p,'benchmark')['active']
            self.activate(b,'second-active',active['activation_sha256'])
            with self.assertRaises(BenchmarkError) as error:self.g.execute_benchmark(self.p,b['config_id'],2,b['configuration_sha256'],ledger,'campaign','second',a)
            self.assertEqual(error.exception.code,'RELEASE_CAMPAIGN_CHANGED');self.assertEqual(ledger.get('attempt'),original)
    def test_no_active_configuration_cannot_evaluate(self):
        r,a=self.save_benchmark()
        with ReleaseLedger(self.root/'evaluation.sqlite3') as ledger:self.error(lambda:self.g.execute_benchmark(self.p,r['config_id'],1,r['configuration_sha256'],ledger,'c','a',a),'benchmark_not_active')
    def test_roster_change_cannot_be_silently_accepted(self):
        c,a=self.benchmark();c['policy']['enterprise']['metrics'].pop()
        self.error(lambda:self.save(c,kind='benchmark'),'benchmark_configuration_invalid')
    def test_duplicate_independence_group_is_rejected(self):
        c,a=self.benchmark();c['policy']['aggregation']['raters'][1]['independence_group']=c['policy']['aggregation']['raters'][0]['independence_group']
        self.error(lambda:self.save(c,kind='benchmark'),'benchmark_configuration_invalid')
    def test_out_of_range_floor_rejected(self):
        c,a=self.benchmark();c['policy']['critical_floors']['floors'][0]['minimum']='2'
        self.error(lambda:self.save(c,kind='benchmark'),'benchmark_configuration_invalid')
    def test_production_floor_weakening_rejected(self):
        c,a=self.benchmark(True);c['policy']['critical_floors']['floors'][0]['minimum']='0'
        self.error(lambda:self.save(c,kind='benchmark'),'benchmark_configuration_invalid')
    def test_production_inputs_without_attestation_block(self):
        c,a=self.benchmark(True);r=self.save(c,kind='benchmark');self.activate(r)
        with ReleaseLedger(self.root/'evaluation.sqlite3') as ledger:v=self.g.execute_benchmark(self.p,r['config_id'],1,r['configuration_sha256'],ledger,'c','a',a)
        self.assertEqual(v['report']['outcome'],'BLOCKED');self.assertIn('MISSING_CANDIDATE_BUNDLE',v['report']['reasons'])
    def test_invalid_secret_or_path_not_saved(self):
        c,a=self.benchmark();c['policy']['id']='C:/user/private'
        with self.assertRaises(OperatorError):self.save(c,kind='benchmark')
    def test_no_http_score_publication_or_runner_registration(self):
        for path in ('governance/benchmark/id/execute','governance/benchmark/id/score','governance/benchmark/id/runner'):
            self.assertEqual(self.post(path,{'score':1}).status_code,404)
    def test_unknown_configuration_field_rejected(self):
        c,a=self.benchmark();c['secret']='PRIVATE';self.error(lambda:self.save(c,kind='benchmark'),'governance_schema_invalid')
    def test_restart_frozen_version_exact_hash(self):
        r,a=self.save_benchmark();self.activate(r)
        self.assertEqual(Service(self.root,self.creds).governance.list(self.p,'benchmark'),self.g.list(self.p,'benchmark'))
    def test_version_change_diff_has_no_evaluation_score_claim(self):
        r,a=self.save_benchmark();c=copy.deepcopy(r['configuration']);c['policy']['enterprise']['minimum_score']='1'
        self.save(c,1,'new',id='benchmark-one',kind='benchmark')
        d=self.g.diff(self.p,'benchmark','benchmark-one',1,2);self.assertEqual(d['changes'][0]['path'],'/policy/enterprise/minimum_score')
        self.assertNotIn('actual_score',json.dumps(self.g.list(self.p,'benchmark')))
    def test_duplicate_import_keys_rejected_without_reserializing(self):
        r=self.client.post('/operator/v1/governance/benchmark/invalid/versions',headers={**self.headers,'Content-Type':'application/json'},
            content=b'{"configuration":{"manifest":{},"manifest":{},"policy":{}},"expected_revision":0,"idempotency_key":"key"}')
        self.assertEqual(r.status_code,400);self.assertEqual(r.json()['error']['code'],'duplicate_json_key')
        js=self.client.get('/static/governance.js').text;self.assertIn('request,false,true',js);self.assertNotIn('JSON.parse(',js)
        self.assertEqual(self.g.list(self.p,'benchmark')['items'],[])
    def test_tenant_and_permissions_enforced(self):
        r,a=self.save_benchmark();self.assertEqual(self.g.list(self.foreign(),'benchmark')['items'],[])
        p,h=self.reader();self.error(lambda:self.g.save(p,'benchmark','other',r['configuration'],0,'x'),'forbidden')
    def test_revoked_config_access_rejected(self):
        self.creds.revoke(self.token);self.error(lambda:self.g.list(self.p,'benchmark'),'unauthorized')

class Admin007(GovernanceBase):
    def test_append_only_config_before_after_actor_timestamp(self):
        r=self.save();self.activate(r);v=self.g.audit(self.p)['items']
        self.assertEqual(v[0]['action'],'CONFIG_VERSION_CREATED');self.assertEqual(v[1]['action'],'CONFIG_ACTIVATED')
        self.assertEqual(v[0]['after_sha256'],r['configuration_sha256']);self.assertIsNone(v[0]['before_sha256'])
        self.assertEqual(v[1]['authorization'],'ALLOW');self.assertEqual(v[1]['actor'],self.p.actor)
    def test_canonical_projection_log_really_verified(self):
        self.save()
        with patch.object(AuditLog,'verify',autospec=True,side_effect=AuditLog.verify) as v:self.g.audit(self.p)
        self.assertEqual(v.call_count,1)
    def test_restart_durable_audit_identical(self):
        self.save();self.assertEqual(Service(self.root,self.creds).governance.audit(self.p),self.g.audit(self.p))
    def test_legacy_resource_event_exactly_attributed(self):
        run=self.make_run();rows=self.g.audit(self.p,target=run)['items']
        self.assertEqual(rows[0]['tenant_attribution'],'EXACT_RESOURCE_BINDING');self.assertEqual(rows[0]['authorization'],'LEGACY_NOT_RECORDED')
    def test_legacy_ambiguous_tenant_never_actor_inferred(self):
        from test_batch003d import NeverInvokedAdapter
        from bie.model_gateway.provider_registry import ProviderDescriptor
        descriptor=ProviderDescriptor('local-test','registry-only',frozenset({'text'}),True)
        self.service.administration.provision_provider(self.p,descriptor,NeverInvokedAdapter(),evidence_origin='SYNTHETIC_TEST')
        self.service.administration.provision_provider(self.foreign(),descriptor,NeverInvokedAdapter(),evidence_origin='SYNTHETIC_TEST')
        self.assertEqual(self.g.audit(self.p)['items'],[])
    def test_explicit_tenant_same_id_isolated(self):
        self.save();p=self.foreign();self.g.save(p,'policy','policy-one',self.policy('hi'),0,'x')
        a=self.g.audit(self.p)['items'];b=self.g.audit(p)['items'];self.assertEqual(len(a),1);self.assertEqual(len(b),1)
        self.assertNotEqual(a[0]['after_sha256'],b[0]['after_sha256'])
    def test_legacy_unowned_event_omitted(self):
        with self.service.catalog.tx() as db:self.service.catalog.event(db,self.p.actor,'LOCAL_EVENT','unowned')
        self.assertEqual(self.g.audit(self.p)['items'],[])
    def test_unknown_details_never_echo_secret_or_path(self):
        self.save()
        with self.service.catalog.tx() as db:self.service.catalog.event(db,self.p.actor,'OPERATOR_NOTE','policy-one',
            {'secret':'PRIVATE C:/user/path'},tenant=self.p.tenant)
        r=self.g.audit(self.p);self.assertNotIn('PRIVATE',json.dumps(r));self.assertTrue(all(not v['details_exposed'] for v in r['items']))
    def test_event_body_corruption_fails_closed(self):
        self.save()
        with sqlite3.connect(self.service.catalog.path) as db:db.execute("UPDATE audit SET body='{}'")
        self.error(lambda:self.g.audit(self.p),'catalog_tampered')
    def test_deleted_event_fails_closed(self):
        self.save()
        with sqlite3.connect(self.service.catalog.path) as db:db.execute('DELETE FROM audit')
        self.error(lambda:self.g.audit(self.p),'catalog_missing_history')
    def test_modified_sequence_or_previous_hash_rejected(self):
        self.save()
        with sqlite3.connect(self.service.catalog.path) as db:db.execute("UPDATE audit SET prev='wrong'")
        self.error(lambda:self.g.audit(self.p),'catalog_tampered')
    def test_no_http_mutation_or_chain_rewrite(self):
        for method in ('POST','DELETE','PATCH'):
            self.assertEqual(self.client.request(method,'/operator/v1/admin/audit',headers=self.headers,json={}).status_code,405)
    def test_pagination_order_and_filter(self):
        r=self.save();self.activate(r);a=self.g.audit(self.p,limit=1);b=self.g.audit(self.p,a['next_after'],1)
        self.assertGreater(b['items'][0]['sequence'],a['items'][0]['sequence'])
        self.assertEqual(len(self.g.audit(self.p,action='CONFIG_ACTIVATED')['items']),1)
    def test_bounded_scan_progresses_through_invisible_rows(self):
        with self.service.catalog.tx() as db:
            for n in range(257):self.service.catalog.event(db,self.p.actor,'LOCAL_EVENT','unowned')
        self.save();a=self.g.audit(self.p);self.assertEqual(a['items'],[]);self.assertEqual(a['next_after'],256)
        self.assertEqual(len(self.g.audit(self.p,a['next_after'])['items']),1)
    def test_invalid_pagination_and_injection_filter_rejected(self):
        for kwargs in ({'limit':True},{'limit':51},{'after':-1},{'action':'DROP TABLE'},{'target':'../private'}):
            with self.assertRaises(OperatorError):self.g.audit(self.p,**kwargs)
    def test_expired_or_revoked_access_rejected(self):
        self.creds.revoke(self.token);self.assertEqual(self.get('admin/audit').status_code,401)
    def test_read_does_not_add_events_or_change_state(self):
        self.save()
        with self.service.catalog.tx(read_only=True) as db:before=db.execute('SELECT n,sha FROM audit').fetchall()
        a=self.g.audit(self.p);b=self.g.audit(self.p);self.assertEqual(a,b)
        with self.service.catalog.tx(read_only=True) as db:self.assertEqual(list(map(tuple,before)),list(map(tuple,db.execute('SELECT n,sha FROM audit').fetchall())))
    def test_external_notarization_and_privileged_protection_not_claimed(self):
        self.save();a=self.g.audit(self.p);self.assertFalse(a['external_notarization']);self.assertFalse(a['privileged_rewrite_protected'])

TASK_CLASSES={'BIE-APP-ADMIN-005':Admin005,'BIE-APP-ADMIN-006':Admin006,'BIE-APP-ADMIN-007':Admin007}
def selected_suite(task=None):
    suite=unittest.TestSuite()
    for id,cls in TASK_CLASSES.items():
        if task is None or task==id:
            for name in sorted(cls.__dict__):
                if name.startswith('test_'):suite.addTest(cls(name))
    return suite
if __name__=='__main__':raise SystemExit(not unittest.TextTestRunner(verbosity=2).run(selected_suite()).wasSuccessful())
