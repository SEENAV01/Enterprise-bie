"""H1-002 actual catalogue bounds, canonical worker credits and seeded faults."""
from pathlib import Path
import dataclasses,json,sqlite3,sys,unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).parent))
from test_batch001 import Base,DATA,structural_pdf
from apps.operator.catalog import Catalog
from apps.operator.catalog_budget import CatalogBudget
from apps.operator.contracts import OperatorError,canonical,digest
from apps.operator.service import Service
from apps.operator.artifacts import ProductArtifacts

class CatalogHardening(Base):
    def stats(self):
        with self.service.catalog.tx(read_only=True) as db:return self.service.catalog.budget.inventory(db)
    def cap(self,**limits):
        self.service.catalog.budget=dataclasses.replace(self.service.catalog.budget,**limits)
    def fill(self):
        source=self.source();self.cap(max_events=self.stats()['events']);return source
    def raw(self,statement,args=()):
        with sqlite3.connect(self.service.catalog.path) as db:db.execute(statement,args)

    def test_default_limits_and_immutable_configuration(self):
        b=CatalogBudget();self.assertEqual(b.max_events,65536);self.assertEqual(b.max_state_rows,32768)
        with self.assertRaises(dataclasses.FrozenInstanceError):b.max_events=5
    def test_invalid_budget_bounds_rejected(self):
        for value in (True,0,-1,65537,'10'):
            with self.subTest(value=value):self.error(lambda:CatalogBudget(max_events=value),'catalog_budget_invalid')
    def test_invalid_budget_object_rejected(self):
        self.error(lambda:Catalog(self.root,budget={}), 'catalog_budget_invalid')
    def test_old_source_producer_cannot_bypass_global_cap(self):
        self.fill()
        with patch('apps.operator.service.inspect_real_pdf') as inspector:
            self.error(lambda:self.source(structural_pdf(2)),'audit_capacity_reached')
        inspector.assert_not_called();self.assertEqual(self.stats()['events'],1)
    def test_run_creation_denied_before_canonical_submission(self):
        source=self.fill()
        with patch.object(self.service,'native') as native:
            self.error(lambda:self.service.create(self.p,source['source_id'],{},'new'),'audit_capacity_reached')
        native.assert_not_called()
    def test_graph_publication_denied_before_native_writes(self):
        run=self.make_run();source_hash=self.source()['sha256'];self.cap(max_events=self.stats()['events'])
        with patch.object(self.service,'native') as native:
            self.error(lambda:self.service.publish_graph(self.p,run,'concept',dict(source_hash=source_hash,
                nodes=[{'id':'a','label':'node'}],edges=[]),evidence_origin='SYNTHETIC_TEST'),'audit_capacity_reached')
        native.assert_not_called()
    def test_code_publication_cannot_bypass_global_cap(self):
        run=self.make_run();self.cap(max_events=self.stats()['events'])
        with patch.object(self.service,'native') as native:
            self.error(lambda:ProductArtifacts(self.service).publish_code(self.p,run,'print(1)','python',
                evidence_origin='SYNTHETIC_TEST'),'audit_capacity_reached')
        native.assert_not_called()
    def test_provider_and_config_events_use_same_catalogue_guard(self):
        self.fill()
        for action in ('PROVIDER_PROVISIONED','CONFIG_VERSION_CREATED','QUALITY_RECEIPT_BOUND','PREVIEW_BOUND'):
            with self.subTest(action=action):
                def emit():
                    with self.service.catalog.tx() as db:self.service.catalog.event(db,'producer',action,'resource')
                self.error(emit,'audit_capacity_reached')
    def test_exact_limit_keeps_source_readable(self):
        source=self.fill();self.assertEqual(self.service.source(self.p,source['source_id'])['sha256'],source['sha256'])
    def test_exact_limit_keeps_status_and_timeline_readable(self):
        run=self.make_run();self.cap(max_events=self.stats()['events'])
        self.assertEqual(self.service.status(self.p,run)['status'],'READY')
        self.assertTrue(self.service.timeline(self.p,run)['items'])
        self.assertEqual(self.service.list_runs(self.p)['items'][0]['run_id'],run)
    def test_exact_limit_keeps_audit_verified_and_complete(self):
        self.fill();audit=self.service.governance.audit(self.p)
        self.assertEqual(len(audit['items']),1);self.assertTrue(audit['durable_chain_verified'])
    def test_http_capacity_error_is_safe_and_reads_still_work(self):
        source=self.fill()
        response=self.client.post('/operator/v1/sources',headers=dict(self.headers,**{'Content-Type':'application/pdf'}),
            content=structural_pdf(2))
        self.assertEqual(response.status_code,429);self.assertEqual(response.json()['error']['code'],'audit_capacity_reached')
        for text in ('Traceback',str(self.root),'sqlite','structural runtime fixture'):
            self.assertNotIn(text,response.text)
        self.assertEqual(self.get('sources/'+source['source_id']).status_code,200)
    def test_revoked_access_remains_unauthorized_not_quota_disclosure(self):
        source=self.fill();self.creds.revoke(self.token)
        self.assertEqual(self.get('sources/'+source['source_id']).status_code,401)
    def test_worker_needs_three_receipts_before_dispatch(self):
        run=self.make_run();self.cap(max_events=self.stats()['events']+2)
        with patch.object(self.service,'native') as native:
            self.error(lambda:self.service.work_once(self.p,run),'audit_capacity_reached')
        native.assert_not_called()
        with self.service.catalog.tx(read_only=True) as db:self.assertEqual(db.execute('SELECT COUNT(*) FROM workers').fetchone()[0],0)
    def test_worker_succeeds_at_exact_reserved_capacity(self):
        run=self.make_run();self.cap(max_events=self.stats()['events']+3)
        try:
            result=self.service.work_once(self.p,run)
        except OperatorError as exc:
            self.fail('Canonical worker did not complete: '+exc.code)
        self.assertEqual(result['outcome'],'ACKED')
        self.assertEqual(self.service.status(self.p,run)['status'],'SUCCEEDED')
        self.assertEqual(self.stats()['reserved'],0);self.assertEqual(self.stats()['events'],5)
        self.assertEqual(self.service.administration.workers(self.p)['items'][0]['lifecycle'],'STOPPED')
    def test_other_producer_cannot_steal_worker_completion_credits(self):
        run=self.make_run();self.cap(max_events=self.stats()['events']+3)
        worker=self.service.administration.begin_worker(self.p,run)
        with patch('apps.operator.service.inspect_real_pdf') as inspector:
            self.error(lambda:self.source(structural_pdf(2)),'audit_capacity_reached')
        inspector.assert_not_called()
        result=self.service._execute_once(self.p,run,worker)
        self.service.administration.finish_worker(self.p,worker,result['outcome'])
        self.assertEqual(self.stats()['reserved'],0);self.assertEqual(self.service.status(self.p,run)['status'],'SUCCEEDED')
    def test_reservation_survives_service_restart(self):
        run=self.make_run();worker=self.service.administration.begin_worker(self.p,run)
        replacement=Service(self.root,self.creds)
        with replacement.catalog.tx(read_only=True) as db:
            self.assertEqual(replacement.catalog.budget.inventory(db)['reserved'],2)
        result=replacement._execute_once(self.p,run,worker);replacement.administration.finish_worker(self.p,worker,result['outcome'])
        self.assertEqual(replacement.status(self.p,run)['status'],'SUCCEEDED')
    def test_paused_worker_releases_unused_credit_without_execution(self):
        run=self.make_run();self.service.control(self.p,run,'pause',1)
        self.assertEqual(self.service.work_once(self.p,run)['outcome'],'PAUSED')
        self.assertEqual(self.stats()['reserved'],0);self.assertEqual(self.service.status(self.p,run)['status'],'PAUSED')
    def test_reservation_tamper_is_detected(self):
        run=self.make_run();worker=self.service.administration.begin_worker(self.p,run)
        self.raw('UPDATE audit_reservations SET credits=1 WHERE id=?',(worker,))
        self.error(lambda:self.service.status(self.p,run),'catalog_state_tampered')
    def test_unknown_reservation_cannot_open_write_transaction(self):
        def attempt():
            with self.service.catalog.tx(reservation='worker-missing'):pass
        self.error(attempt,'audit_reservation_missing')
    def test_reserved_byte_headroom_required_before_worker_dispatch(self):
        run=self.make_run();stats=self.stats();b=self.service.catalog.budget
        self.cap(max_history_bytes=stats['history_bytes']+2*b.max_row_bytes)
        self.error(lambda:self.service.work_once(self.p,run),'audit_byte_capacity_reached')
        self.assertEqual(self.stats()['reserved'],0)
    def test_oversized_database_rejected_before_sqlite_connection(self):
        self.cap(max_database_bytes=1)
        with patch('apps.operator.catalog.sqlite3.connect',side_effect=OperatorError('seed_connection_called')) as connect:
            self.error(lambda:self.stats(),'catalog_storage_capacity_reached')
        connect.assert_not_called()
    def test_oversized_wal_rejected_before_sqlite_connection(self):
        self.cap(max_wal_bytes=1);wal=Path(str(self.service.catalog.path)+'-wal')
        wal.write_bytes(b'x'*2)
        with patch('apps.operator.catalog.sqlite3.connect') as connect:
            self.error(lambda:self.stats(),'catalog_storage_capacity_reached')
        connect.assert_not_called()
    def test_oversized_shared_memory_sidecar_rejected(self):
        shm=Path(str(self.service.catalog.path)+'-shm')
        with shm.open('wb') as stream:stream.truncate(1024*1024+1)
        self.error(lambda:self.stats(),'catalog_storage_capacity_reached')
    def test_oversized_history_row_rejected_before_json_decoding(self):
        self.source();self.raw('UPDATE audit SET body=? WHERE n=1',('x'*32769,))
        with patch('apps.operator.catalog.json.loads',side_effect=OperatorError('seed_decoding_called')) as decode:
            self.error(lambda:self.stats(),'catalog_row_capacity_reached')
        decode.assert_not_called()
    def test_state_row_limit_rejected_before_projection_materialization(self):
        self.source();self.cap(max_state_rows=1)
        self.error(lambda:self.source(structural_pdf(2)),'catalog_state_capacity_reached')
        self.assertEqual(self.stats()['state_rows'],1)
    def test_state_byte_limit_fails_closed_without_truncation(self):
        self.source();self.cap(max_state_bytes=self.stats()['state_bytes']-1)
        self.error(lambda:self.stats(),'catalog_state_capacity_reached')
        self.cap(max_state_bytes=16*1024*1024);self.assertEqual(self.stats()['state_rows'],1)
    def test_history_byte_limit_fails_closed_without_pruning(self):
        self.source();self.cap(max_history_bytes=self.stats()['history_bytes']-1)
        self.error(lambda:self.stats(),'audit_byte_capacity_reached')
        self.cap(max_history_bytes=32*1024*1024);self.assertEqual(self.stats()['events'],1)
    def test_oversized_new_event_rolls_back_catalogue_changes(self):
        def emit():
            with self.service.catalog.tx() as db:
                self.service.catalog.event(db,'actor','ADVERSARIAL','target',{'literal':'x'*32769})
        self.error(emit,'catalog_row_capacity_reached');self.assertEqual(self.stats()['events'],0)
    def test_audit_tail_outside_ceiling_rejected_before_hash_replay(self):
        self.source();self.raw('UPDATE audit SET n=65537 WHERE n=1')
        with patch('apps.operator.catalog.digest') as digest:
            self.error(lambda:self.stats(),'audit_capacity_reached')
        digest.assert_not_called()
    def test_read_only_transaction_cannot_write(self):
        def emit():
            with self.service.catalog.tx(read_only=True) as db:
                db.execute("INSERT INTO sources VALUES('bad','bad','{}')")
        self.error(emit,'storage_busy_or_unavailable');self.assertEqual(self.stats()['state_rows'],0)
    def test_integrity_is_replayed_not_cached(self):
        self.source();self.stats()
        with sqlite3.connect(self.service.catalog.path) as db:
            body=json.loads(db.execute('SELECT body FROM audit WHERE n=1').fetchone()[0]);body['action']='ALTERED'
            db.execute('UPDATE audit SET body=? WHERE n=1',(canonical(body).decode(),))
        self.error(lambda:self.stats(),'catalog_tampered')
    def test_legacy_projection_hash_stays_valid_without_reservations(self):
        self.source();before=self.stats()
        replacement=Service(self.root,self.creds)
        with replacement.catalog.tx(read_only=True) as db:
            legacy={t:[list(r) for r in db.execute('SELECT * FROM '+t+' ORDER BY 1,2')]
                    for t in ('sources','intents','graphs')}
            self.assertEqual(replacement.catalog.projection(db),digest(legacy))
            self.assertEqual(json.loads(db.execute('SELECT body FROM audit ORDER BY n DESC LIMIT 1').fetchone()[0])['projection'],digest(legacy))
            self.assertEqual(replacement.catalog.budget.inventory(db),before)
    def test_full_128_event_history_verified_without_cache_or_truncation(self):
        with self.service.catalog.tx() as db:
            for n in range(128):self.service.catalog.event(db,'producer','MEASURED_HISTORY','item-'+str(n))
        from apps.operator.catalog import digest as original
        with patch('apps.operator.catalog.digest',wraps=original) as verifier:
            with self.service.catalog.tx(read_only=True) as db:
                self.assertEqual(db.execute('SELECT COUNT(*) FROM audit').fetchone()[0],128)
        self.assertGreaterEqual(verifier.call_count,129)
        self.assertEqual(self.stats()['events'],128)
    def test_foreign_tenant_cannot_finish_reserved_worker(self):
        from apps.operator.contracts import Principal,PERMISSIONS
        import secrets,time
        run=self.make_run();worker=self.service.administration.begin_worker(self.p,run)
        foreign=Principal('other','foreign',PERMISSIONS,time.time()+600);self.creds.grant(secrets.token_hex(32),foreign)
        self.error(lambda:self.service.administration.finish_worker(foreign,worker,'INTERRUPTED'),'worker_not_found')
        self.assertEqual(self.stats()['reserved'],2)
        self.service.administration.finish_worker(self.p,worker,'INTERRUPTED');self.assertEqual(self.stats()['reserved'],0)

TASK_CLASSES={'BIE-APP-H1-002':CatalogHardening}
def selected_suite(task=None):
    return unittest.defaultTestLoader.loadTestsFromTestCase(CatalogHardening)
if __name__=='__main__':unittest.main(verbosity=2)
