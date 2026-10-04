"""H1-005: actual crash/restart reservation recovery, not fabricated job states."""
from pathlib import Path
import json,os,subprocess,sys,time,unittest
from test_batch001 import Base
from apps.operator.contracts import digest,Principal,PERMISSIONS
from apps.operator.service import Service

CHILD='''import os,secrets,sys,time
from pathlib import Path
from apps.operator.contracts import Credentials,Principal,PERMISSIONS
from apps.operator.service import Service
c=Credentials();p=Principal('test-operator','tenant-a',PERMISSIONS,time.time()+3600)
c.grant(secrets.token_hex(32),p);s=Service(Path(sys.argv[1]),c)
w=s.administration.begin_worker(p,sys.argv[2])
print(w,flush=True)
if sys.argv[3]=='execute':s._execute_once(p,sys.argv[2],w)
os._exit(74)
'''
RECOVER_CHILD='''import json,secrets,sys,time
from pathlib import Path
from apps.operator.contracts import Credentials,Principal,PERMISSIONS
from apps.operator.service import Service
c=Credentials();p=Principal('test-operator','tenant-a',PERMISSIONS,time.time()+3600)
c.grant(secrets.token_hex(32),p);s=Service(Path(sys.argv[1]),c)
deadline=time.monotonic()+10
while not Path(sys.argv[5]).exists():
    if time.monotonic()>deadline:raise SystemExit(73)
    time.sleep(.005)
r=s.administration.reconcile_worker(p,sys.argv[2],sys.argv[3],sys.argv[4])
print(json.dumps(r,sort_keys=True),flush=True)
'''
class WorkerRecovery(Base):
    def crash(self,run,mode='ready'):
        env={k:v for k,v in os.environ.items() if k in ('PATH','SystemRoot','TEMP','TMP','WINDIR')}
        env.update(PYTHONPATH=str(Path(__file__).resolve().parents[2]),PYTHONUTF8='1',PYTHONDONTWRITEBYTECODE='1')
        process=subprocess.Popen([sys.executable,'-B','-c',CHILD,str(self.root),run,mode],env=env,
            stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        try:
            stdout,stderr=process.communicate(timeout=20)
            self.assertEqual(process.returncode,74,stderr)
            return stdout.strip()
        finally:
            if process.poll() is None:process.kill()
            process.wait(timeout=5)
            process.stdout.close();process.stderr.close()
    def body(self,worker):
        with self.service.catalog.tx(read_only=True) as db:
            return json.loads(db.execute('SELECT body FROM workers WHERE id=?',(worker,)).fetchone()[0])
    def stats(self):
        with self.service.catalog.tx(read_only=True) as db:return self.service.catalog.budget.inventory(db)
    def request(self,worker,key='recover',expected=None):
        return dict(expected_record_sha256=digest(self.body(worker)) if expected is None else expected,
                    idempotency_key=key)
    def recover(self,worker,request):return self.post('admin/workers/'+worker+'/reconcile',request)
    def test_actual_pre_dispatch_process_crash_has_governed_recovery_after_restart(self):
        run=self.make_run();before=self.service.status(self.p,run);worker=self.crash(run)
        self.assertEqual(self.stats()['reserved'],2)
        self.service=Service(self.root,self.creds);self.client.app.state.operator_service=self.service
        # Rebuild the app too: routes close over their own verified service.
        from fastapi.testclient import TestClient
        from apps.operator.main import create_app
        self.client.close();self.client=TestClient(create_app(self.service),base_url='http://localhost',raise_server_exceptions=False)
        response=self.recover(worker,self.request(worker))
        self.assertEqual(response.status_code,200,response.text)
        self.assertEqual(response.json()['scope'],'DISPATCH_ADMISSION_ONLY')
        self.assertFalse(response.json()['process_termination_claimed'])
        self.assertEqual(self.stats()['reserved'],0)
        after=self.service.status(self.p,run)
        for field in ('run_id','native_job_id','source_hash','config_hash','engine_state','queue_state','status'):
            self.assertEqual(before[field],after[field])
        self.assertEqual(after['status'],'READY')
    def test_actual_post_native_process_crash_keeps_success_and_releases_credit(self):
        run=self.make_run();worker=self.crash(run,'execute');request=self.request(worker)
        self.assertEqual(self.stats()['reserved'],1)
        before=self.service.result(self.p,run)
        response=self.recover(worker,request)
        self.assertEqual(response.status_code,200,response.text)
        self.assertEqual(response.json()['outcome'],'TERMINAL')
        self.assertEqual(self.stats()['reserved'],0)
        self.assertEqual(self.service.status(self.p,run)['status'],'SUCCEEDED')
        self.assertEqual(self.service.result(self.p,run),before)
    def test_same_intent_replay_has_one_audit_and_no_second_credit_release(self):
        run=self.make_run();worker=self.crash(run);request=self.request(worker)
        first=self.recover(worker,request);count=self.stats()['events']
        second=self.recover(worker,request)
        self.assertEqual((first.status_code,second.status_code),(200,200))
        self.assertFalse(first.json()['replayed']);self.assertTrue(second.json()['replayed'])
        self.assertEqual(self.stats()['events'],count);self.assertEqual(self.stats()['reserved'],0)
    def test_replay_at_exact_audit_capacity_remains_read_only(self):
        from dataclasses import replace
        run=self.make_run();worker=self.crash(run);request=self.request(worker)
        self.assertEqual(self.recover(worker,request).status_code,200)
        self.service.catalog.budget=replace(self.service.catalog.budget,max_events=self.stats()['events'])
        self.assertEqual(self.recover(worker,request).status_code,200)
    def test_changed_retry_key_cannot_reconcile_a_finished_worker_again(self):
        run=self.make_run();worker=self.crash(run);request=self.request(worker)
        self.assertEqual(self.recover(worker,request).status_code,200)
        request['idempotency_key']='different-key'
        response=self.recover(worker,request)
        self.assertEqual(response.status_code,409);self.assertEqual(response.json()['error']['code'],'idempotency_conflict')
    def test_stale_record_is_rejected_without_releasing_reserved_credits(self):
        run=self.make_run();worker=self.crash(run)
        response=self.recover(worker,self.request(worker,expected='0'*64))
        self.assertEqual(response.status_code,409);self.assertEqual(response.json()['error']['code'],'stale_worker_record')
        self.assertEqual(self.stats()['reserved'],2)
    def test_late_dispatch_is_fenced_and_ready_job_is_not_falsely_failed(self):
        run=self.make_run();worker=self.crash(run)
        self.assertEqual(self.recover(worker,self.request(worker)).status_code,200)
        self.error(lambda:self.service._execute_once(self.p,run,worker),'worker_dispatch_fenced')
        self.assertEqual(self.service.status(self.p,run)['status'],'READY')
    def test_running_delivery_requires_review_not_heartbeat_death_inference(self):
        from apps.api.job_service import CAPABILITY
        run=self.make_run();worker=self.service.administration.begin_worker(self.p,run)
        with self.service.catalog.tx(read_only=True) as db:_,body=self.service.catalog.intent(db,self.p,run)
        with self.service.native(body) as native:
            q=native.queue.poll(worker,capability_tags=[CAPABILITY])
            source='source-'+body['native_job_id'][4:]
            native._transition(body['native_job_id'],'READY','RUNNING',input_refs=[source],reason='worker_started')
        response=self.recover(worker,self.request(worker))
        self.assertEqual(response.status_code,409)
        self.assertEqual(response.json()['error']['code'],'worker_recovery_requires_quiescent_state')
        self.assertEqual(self.service.status(self.p,run)['status'],'RUNNING');self.assertEqual(self.stats()['reserved'],2)
    def test_foreign_tenant_cannot_reconcile_or_discover_dispatch(self):
        import secrets
        run=self.make_run();worker=self.crash(run);request=self.request(worker)
        token=secrets.token_hex(32);p=Principal('foreign','tenant-b',PERMISSIONS,time.time()+3600)
        self.creds.grant(token,p)
        response=self.client.post('/operator/v1/admin/workers/'+worker+'/reconcile',
            headers={'Authorization':'Bearer '+token},json=request)
        self.assertEqual(response.status_code,404);self.assertEqual(self.stats()['reserved'],2)
    def test_revoked_principal_is_rejected_before_recovery_or_quota_disclosure(self):
        run=self.make_run();worker=self.crash(run);request=self.request(worker)
        self.creds.revoke(self.token)
        self.assertEqual(self.recover(worker,request).status_code,401)
        self.assertEqual(self.stats()['reserved'],2)
    def test_recovery_permission_is_required(self):
        import secrets
        run=self.make_run();worker=self.crash(run);request=self.request(worker)
        token=secrets.token_hex(32);p=Principal('reader','tenant-a',frozenset({'read','admin_read'}),time.time()+3600)
        self.creds.grant(token,p)
        response=self.client.post('/operator/v1/admin/workers/'+worker+'/reconcile',
            headers={'Authorization':'Bearer '+token},json=request)
        self.assertEqual(response.status_code,403);self.assertEqual(self.stats()['reserved'],2)
    def test_worker_view_exposes_verified_recovery_pin_not_secret_or_fake_death(self):
        run=self.make_run();worker=self.crash(run)
        view=self.get('admin/workers').json()['items'][0]
        self.assertEqual(view['record_sha256'],digest(self.body(worker)));self.assertTrue(view['can_reconcile'])
        self.assertFalse(view['death_inferred_from_stale']);self.assertNotIn(self.token,json.dumps(view))
    def test_same_intent_competing_threads_release_credit_exactly_once(self):
        from concurrent.futures import ThreadPoolExecutor
        run=self.make_run();worker=self.crash(run);request=self.request(worker)
        def recover():return self.service.administration.reconcile_worker(self.p,worker,
            request['expected_record_sha256'],request['idempotency_key'])
        before=self.stats()['events']
        with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(lambda _:recover(),range(2)))
        self.assertEqual(sorted(r['replayed'] for r in results),[False,True])
        self.assertEqual(self.stats()['events'],before+1);self.assertEqual(self.stats()['reserved'],0)
    def test_actual_cas_exhaustion_finishes_failed_without_invented_evidence(self):
        from apps.operator.cas_budget import CASLimits
        from test_batch001 import DATA
        from apps.operator.contracts import OperatorError
        # Measure real source/config storage, then use a fresh governed root at
        # exactly that capacity. No policy mutation or oversize real fixture.
        measured=self.make_run();used=self.service.cas_budget.inventory()['bytes']
        limited=Service(self.root/'limited',self.creds,cas_limits=CASLimits(max_bytes=used))
        source=limited.import_pdf(self.p,DATA)
        run=limited.create(self.p,source['source_id'],{},'test-run')['run_id']
        self.assertEqual(limited.cas_budget.inventory()['bytes'],used)
        result=limited.work_once(self.p,run)
        self.assertEqual(result['outcome'],'FAILED')
        state=limited.status(self.p,run)
        self.assertEqual((state['status'],state['queue_state'],state['result_available']),('FAILED','DEAD_LETTER',False))
        failure=limited.failure(self.p,run)
        self.assertEqual(failure['diagnostic_codes'],['cas_capacity_reached']);self.assertEqual(failure['evidence_refs'],[])
        self.assertEqual(limited.cas_budget.inventory()['bytes'],used)
        with limited.catalog.tx(read_only=True) as db:self.assertEqual(limited.catalog.budget.inventory(db)['reserved'],0)
    def test_real_completion_reconciliation_cut_has_no_double_finish_or_stranded_credit(self):
        from contextlib import contextmanager
        from concurrent.futures import ThreadPoolExecutor
        from threading import Event,get_ident
        from unittest.mock import patch
        run=self.make_run();worker=self.service.administration.begin_worker(self.p,run)
        outcome=self.service._execute_once(self.p,run,worker)['outcome']
        request=self.request(worker);before=self.stats()['events'];entered=Event();release=Event();thread_id=[]
        original=self.service.catalog.tx
        @contextmanager
        def scheduled(*args,**kwargs):
            if kwargs.get('reservation')==worker and thread_id and get_ident()==thread_id[0]:
                entered.set()
                if not release.wait(10):raise RuntimeError('actual scheduling control timed out')
            with original(*args,**kwargs) as db:yield db
        def finish():
            thread_id.append(get_ident());self.service.administration.finish_worker(self.p,worker,outcome)
        with patch.object(self.service.catalog,'tx',scheduled),ThreadPoolExecutor(max_workers=1) as pool:
            future=pool.submit(finish)
            try:
                self.assertTrue(entered.wait(10))
                result=self.service.administration.reconcile_worker(self.p,worker,
                    request['expected_record_sha256'],request['idempotency_key'])
                self.assertEqual(result['engine_state'],'SUCCEEDED')
            finally:release.set()
            future.result(timeout=10)
        self.assertEqual(self.stats()['reserved'],0)
        self.assertEqual(self.stats()['events'],before+1)
        self.assertEqual(self.service.status(self.p,run)['status'],'SUCCEEDED')
    def test_missing_credit_without_durable_reconciliation_is_not_silently_swallowed(self):
        run=self.make_run();worker=self.service.administration.begin_worker(self.p,run)
        # A real, hash-bound reservation consumption without a settled worker
        # record models an incomplete internal operation, not a fake exception.
        with self.service.catalog.tx(reservation=worker) as db:
            self.service.catalog.event(db,self.p.actor,'SYNTHETIC_INTERRUPTED_COMPLETION',worker,
                                       reservation=worker,final_reservation=True)
        self.error(lambda:self.service.administration.finish_worker(self.p,worker,'IDLE'),
                   'audit_reservation_missing')
        self.assertEqual(self.body(worker)['state'],'DISPATCHING')
        self.assertEqual(self.service.status(self.p,run)['status'],'READY')
    def test_actual_competing_processes_reconcile_one_intent_once_after_crash(self):
        run=self.make_run();worker=self.crash(run);request=self.request(worker)
        before=self.stats()['events'];gate=self.root/'recovery-release';processes=[]
        env={k:v for k,v in os.environ.items() if k in ('PATH','SystemRoot','TEMP','TMP','WINDIR')}
        root=Path(__file__).resolve().parents[2]
        env.update(PYTHONPATH=str(root),PYTHONUTF8='1',PYTHONDONTWRITEBYTECODE='1')
        try:
            for _ in range(2):
                processes.append(subprocess.Popen([sys.executable,'-B','-c',RECOVER_CHILD,str(self.root),worker,
                    request['expected_record_sha256'],request['idempotency_key'],str(gate)],cwd=root,env=env,
                    stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True))
            gate.write_bytes(b'go')
            results=[]
            for process in processes:
                stdout,stderr=process.communicate(timeout=20)
                self.assertEqual(process.returncode,0,stderr);results.append(json.loads(stdout))
            self.assertEqual(sorted(r['replayed'] for r in results),[False,True])
            self.assertEqual({r['worker_id'] for r in results},{worker})
        finally:
            for process in processes:
                if process.poll() is None:process.kill()
                process.wait(timeout=5);process.stdout.close();process.stderr.close()
        self.assertEqual(self.stats()['reserved'],0);self.assertEqual(self.stats()['events'],before+1)
        self.assertEqual(self.service.status(self.p,run)['status'],'READY')
