"""Real terminal worker crash cuts; no re-extraction, forged success or retry."""
from pathlib import Path
import json,os,subprocess,sys,unittest
from test_worker_recovery import WorkerRecovery
from test_batch001 import Base
from apps.operator.contracts import OperatorError

CHILD='''import os,secrets,sys,time
from pathlib import Path
from apps.operator.contracts import Credentials,Principal,PERMISSIONS
from apps.operator.service import Service
from bie.infrastructure.durable_task_queue import SQLiteDurableTaskQueue
from bie.infrastructure.idempotency_store import SQLiteIdempotencyStore
c=Credentials();p=Principal('test-operator','tenant-a',PERMISSIONS,time.time()+3600)
c.grant(secrets.token_hex(32),p);s=Service(Path(sys.argv[1]),c)
w=s.administration.begin_worker(p,sys.argv[2]);print(w,flush=True)
if sys.argv[3]=='ack':SQLiteDurableTaskQueue.ack=lambda *args,**kwargs:os._exit(75)
elif sys.argv[3]=='idempotency':SQLiteIdempotencyStore.complete=lambda *args,**kwargs:os._exit(75)
else:raise SystemExit(76)
s._execute_once(p,sys.argv[2],w)
raise SystemExit(77)
'''
class TerminalWorkerRecovery(Base):
    # Reuse four helpers, never inherit/count the existing17 tests again.
    body=WorkerRecovery.body;stats=WorkerRecovery.stats
    request=WorkerRecovery.request;recover=WorkerRecovery.recover
    def terminal_cut(self,mode='ack'):
        run=self.make_run();before=self.service.status(self.p,run)
        env={k:v for k,v in os.environ.items() if k in ('PATH','SystemRoot','TEMP','TMP','WINDIR')}
        root=Path(__file__).resolve().parents[2]
        env.update(PYTHONPATH=str(root),PYTHONUTF8='1',PYTHONDONTWRITEBYTECODE='1')
        child=subprocess.Popen([sys.executable,'-B','-c',CHILD,str(self.root),run,mode],cwd=root,env=env,
            stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        try:
            out,err=child.communicate(timeout=25);self.assertEqual(child.returncode,75,err);worker=out.strip()
        finally:
            if child.poll() is None:child.kill()
            child.wait(timeout=5);child.stdout.close();child.stderr.close()
        with self.service.catalog.tx(read_only=True) as db:_,body=self.service.catalog.intent(db,self.p,run)
        with self.service.native(body) as native:
            persisted=native.persistence.load_run_state(body['native_job_id'])
            self.assertEqual(persisted['stages']['PDF_INSPECTION']['attempts'][0]['state'],'SUCCEEDED')
            result=native.result(body['native_job_id'])
            self.assertEqual(result['source_hash'],before['source_hash'])
        return run,worker,body,result
    def test_actual_crash_before_ack_is_completed_from_existing_verified_result(self):
        run,worker,body,result=self.terminal_cut();request=self.request(worker)
        response=self.recover(worker,request);self.assertEqual(response.status_code,200,response.text)
        self.assertEqual(self.service.status(self.p,run)['queue_state'],'ACKED')
        self.assertEqual(self.service.result(self.p,run),result)
        self.assertEqual(self.stats()['reserved'],0)
    def test_actual_crash_after_ack_completes_idempotency_without_reexecution(self):
        run,worker,body,result=self.terminal_cut('idempotency')
        response=self.recover(worker,self.request(worker));self.assertEqual(response.status_code,200,response.text)
        with self.service.native(body) as native:
            claim=native.idempotency.get(body['native_key'])
            self.assertEqual(claim.state,'COMPLETED')
            self.assertEqual(claim.result_ref,'result-'+body['native_job_id'][4:])
        self.assertEqual(self.service.result(self.p,run),result)
    def test_partial_terminal_queue_is_not_exposed_as_complete_before_reconciliation(self):
        run,worker,body,result=self.terminal_cut()
        response=self.get('runs/'+run)
        self.assertEqual(response.status_code,409)
        self.assertEqual(response.json()['error']['code'],'native_state_inconsistent')
        self.assertEqual(self.stats()['reserved'],2)
    def test_source_cas_corruption_prevents_terminal_queue_repair(self):
        run,worker,body,result=self.terminal_cut();request=self.request(worker)
        with self.service.native(body) as native:
            record=native.persistence.load_artifact('source-'+body['native_job_id'][4:])
            native.cas._path(record.blob_digest).write_bytes(b'SYNTHETIC_CORRUPTION')
        response=self.recover(worker,request)
        self.assertNotEqual(response.status_code,200)
        with self.service.native(body) as native:
            self.assertEqual(native.queue.get('inspect-'+body['native_job_id'][4:]).state,'DELIVERED')
        self.assertEqual(self.stats()['reserved'],2)
    def test_foreign_idempotency_owner_cannot_be_finalized_or_acknowledged(self):
        run,worker,body,result=self.terminal_cut();request=self.request(worker)
        with self.service.native(body) as native:
            with native.idempotency.db:
                native.idempotency.db.execute('UPDATE claims SET owner=? WHERE key=?',('foreign-owner',body['native_key']))
        response=self.recover(worker,request)
        self.assertEqual(response.status_code,409)
        self.assertEqual(response.json()['error']['code'],'terminal_recovery_idempotency_invalid')
        with self.service.native(body) as native:
            self.assertEqual(native.queue.get('inspect-'+body['native_job_id'][4:]).state,'DELIVERED')
        self.assertEqual(self.stats()['reserved'],2)
    def test_result_cas_corruption_cannot_be_repaired_into_success(self):
        run,worker,body,result=self.terminal_cut();request=self.request(worker)
        with self.service.native(body) as native:
            record=native.persistence.load_artifact('result-'+body['native_job_id'][4:])
            native.cas._path(record.blob_digest).write_bytes(b'SYNTHETIC_CORRUPTION')
        self.assertNotEqual(self.recover(worker,request).status_code,200)
        with self.service.native(body) as native:
            self.assertEqual(native.queue.get('inspect-'+body['native_job_id'][4:]).state,'DELIVERED')
        self.assertEqual(self.stats()['reserved'],2)
    def test_partial_terminal_worker_is_visible_as_review_not_fake_complete(self):
        run,worker,body,result=self.terminal_cut()
        response=self.get('admin/workers');self.assertEqual(response.status_code,200,response.text)
        item=response.json()['items'][0]
        self.assertEqual(item['native_consistency'],'REVIEW_REQUIRED_PARTIAL_FINALIZATION')
        self.assertEqual(item['queue_state'],'DELIVERED');self.assertTrue(item['can_reconcile'])
        self.assertFalse(item['death_inferred_from_stale'])
    def test_actual_reconciliation_crash_after_ack_replays_without_new_inspection(self):
        from unittest.mock import patch
        run,worker,body,result=self.terminal_cut();request=self.request(worker);before=self.stats()['events']
        code='''import os,secrets,sys,time
from pathlib import Path
from apps.operator.contracts import Credentials,Principal,PERMISSIONS
from apps.operator.service import Service
from bie.infrastructure.durable_task_queue import SQLiteDurableTaskQueue
c=Credentials();p=Principal('test-operator','tenant-a',PERMISSIONS,time.time()+3600)
c.grant(secrets.token_hex(32),p);s=Service(Path(sys.argv[1]),c)
original=SQLiteDurableTaskQueue.ack
def cut(*args,**kwargs):original(*args,**kwargs);os._exit(78)
SQLiteDurableTaskQueue.ack=cut
s.administration.reconcile_worker(p,sys.argv[2],sys.argv[3],sys.argv[4])
raise SystemExit(79)
'''
        root=Path(__file__).resolve().parents[2]
        env={k:v for k,v in os.environ.items() if k in ('PATH','SystemRoot','TEMP','TMP','WINDIR')}
        env.update(PYTHONPATH=str(root),PYTHONUTF8='1',PYTHONDONTWRITEBYTECODE='1')
        child=subprocess.Popen([sys.executable,'-B','-c',code,str(self.root),worker,
            request['expected_record_sha256'],request['idempotency_key']],cwd=root,env=env,
            stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        try:
            out,err=child.communicate(timeout=20);self.assertEqual(child.returncode,78,err)
        finally:
            if child.poll() is None:child.kill()
            child.wait(timeout=5);child.stdout.close();child.stderr.close()
        self.assertEqual(self.stats()['events'],before);self.assertEqual(self.stats()['reserved'],2)
        with patch('apps.api.job_service.inspect_real_pdf_toc') as inspector:
            response=self.recover(worker,request);self.assertEqual(response.status_code,200,response.text)
        inspector.assert_not_called()
        self.assertEqual(self.stats()['events'],before+1);self.assertEqual(self.stats()['reserved'],0)
        self.assertEqual(self.service.result(self.p,run),result)
    def test_authenticated_workspace_opens_despite_partial_run_and_restart(self):
        run,worker,body,result=self.terminal_cut()
        self.assertEqual(self.get('runs?limit=1').status_code,409)
        response=self.get('workspace');self.assertEqual(response.status_code,200,response.text)
        self.assertEqual(response.json(),dict(status='AUTHORIZED_WORKSPACE',run_health_checked=False,
            tenant_scoped=True,product_accepted=False))
        self.service=type(self.service)(self.root,self.creds)
        from fastapi.testclient import TestClient
        from apps.operator.main import create_app
        self.client.close()
        self.client=TestClient(create_app(self.service),base_url='http://localhost',raise_server_exceptions=False)
        self.assertIs(self.client.app.state.operator_service,self.service)
        reopened=self.get('workspace');self.assertEqual(reopened.status_code,200,reopened.text)
        self.assertEqual(reopened.json(),response.json())
        self.assertEqual(self.get('runs/'+run).status_code,409)
        self.assertEqual(self.get('admin/workers').json()['items'][0]['native_consistency'],
                         'REVIEW_REQUIRED_PARTIAL_FINALIZATION')
    def test_workspace_without_credentials_fails_closed(self):
        response=self.client.get('/operator/v1/workspace')
        self.assertEqual(response.status_code,401)
    def test_workspace_revoked_credentials_do_not_reopen_recovery(self):
        self.creds.revoke(self.token)
        self.assertEqual(self.get('workspace').status_code,401)
    def test_workspace_cannot_bypass_catalog_tampering(self):
        import sqlite3
        self.make_run()
        with sqlite3.connect(self.service.catalog.path) as db:
            db.execute("UPDATE intents SET control='CANCELLED'")
        response=self.get('workspace');self.assertEqual(response.status_code,409)
        self.assertEqual(response.json()['error']['code'],'catalog_state_tampered')
def selected_suite():
    return unittest.TestSuite(TerminalWorkerRecovery(name) for name in sorted(TerminalWorkerRecovery.__dict__)
                              if name.startswith('test_'))
if __name__=='__main__':unittest.TextTestRunner(verbosity=2).run(selected_suite())
