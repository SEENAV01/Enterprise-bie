"""Actual governed outline failure and process cuts, not a fake exception."""
from pathlib import Path
import os,subprocess,sys,unittest
from test_batch001 import Base,hierarchy_pdf_with_outline
from test_worker_recovery import WorkerRecovery

CHILD='''import os,secrets,sys,time
from pathlib import Path
from apps.operator.contracts import Credentials,Principal,PERMISSIONS
from apps.operator.service import Service
from bie.infrastructure.durable_task_queue import SQLiteDurableTaskQueue
from bie.infrastructure.persistence import SQLitePersistence
c=Credentials();p=Principal('test-operator','tenant-a',PERMISSIONS,time.time()+3600)
c.grant(secrets.token_hex(32),p);s=Service(Path(sys.argv[1]),c)
w=s.administration.begin_worker(p,sys.argv[2]);print(w,flush=True)
if sys.argv[3]=='dead_letter':SQLiteDurableTaskQueue.dead_letter=lambda *args,**kwargs:os._exit(81)
elif sys.argv[3]=='blocked':
    original=SQLitePersistence.set_run_state
    def cut(self,run,state):
        if state=='BLOCKED':os._exit(81)
        return original(self,run,state)
    SQLitePersistence.set_run_state=cut
else:raise SystemExit(82)
s._execute_once(p,sys.argv[2],w)
raise SystemExit(83)
'''
class FailedTerminalRecovery(Base):
    body=WorkerRecovery.body;stats=WorkerRecovery.stats
    request=WorkerRecovery.request;recover=WorkerRecovery.recover
    def failed_cut(self,mode='dead_letter'):
        # A real PDF whose base inventory is valid, but native outline title is
        # empty. The canonical TOC runtime genuinely rejects it in the worker.
        data=hierarchy_pdf_with_outline(((' ',0,None),))
        source=self.source(data);self.assertEqual(source['validation']['status'],'VALID')
        run=self.service.create(self.p,source['source_id'],{},'genuine-failed-cut')['run_id']
        root=Path(__file__).resolve().parents[2]
        env={k:v for k,v in os.environ.items() if k in ('PATH','SystemRoot','TEMP','TMP','WINDIR')}
        env.update(PYTHONPATH=str(root),PYTHONUTF8='1',PYTHONDONTWRITEBYTECODE='1')
        child=subprocess.Popen([sys.executable,'-B','-c',CHILD,str(self.root),run,mode],cwd=root,env=env,
            stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        try:
            out,err=child.communicate(timeout=25);self.assertEqual(child.returncode,81,err);worker=out.strip()
        finally:
            if child.poll() is None:child.kill()
            child.wait(timeout=5);child.stdout.close();child.stderr.close()
        with self.service.catalog.tx(read_only=True) as db:_,body=self.service.catalog.intent(db,self.p,run)
        with self.service.native(body) as native:
            snapshot=native.persistence.load_run_state(body['native_job_id'])
            attempt=snapshot['stages']['PDF_INSPECTION']['attempts'][0]
            self.assertEqual(attempt['state'],'FAILED')
            self.assertEqual(attempt['diagnostics'],['pdf_inspection_failed'])
            self.assertEqual(native.queue.get('inspect-'+body['native_job_id'][4:]).state,'DELIVERED')
        self.assertEqual(self.get('runs/'+run).status_code,409)
        return run,worker,body,source
    def test_actual_failed_before_dead_letter_recovers_failed_state_without_result(self):
        from unittest.mock import patch
        run,worker,body,source=self.failed_cut()
        with patch('apps.api.job_service.inspect_real_pdf_toc') as inspector:
            response=self.recover(worker,self.request(worker))
        self.assertEqual(response.status_code,200,response.text);inspector.assert_not_called()
        state=self.service.status(self.p,run)
        self.assertEqual((state['status'],state['queue_state'],state['result_available']),('FAILED','DEAD_LETTER',False))
        self.assertEqual(state['source_hash'],source['sha256'])
        self.assertEqual(self.service.failure(self.p,run)['diagnostic_codes'],['pdf_inspection_failed'])
        self.assertEqual(self.stats()['reserved'],0)
    def test_real_failure_before_blocked_recovers_only_existing_failed_evidence(self):
        run,worker,body,source=self.failed_cut('blocked')
        response=self.recover(worker,self.request(worker));self.assertEqual(response.status_code,200,response.text)
        state=self.service.status(self.p,run)
        self.assertEqual((state['engine_run_state'],state['status'],state['queue_state']),('BLOCKED','FAILED','DEAD_LETTER'))
        with self.service.native(body) as native:
            claim=native.idempotency.get(body['native_key'])
            self.assertEqual((claim.state,claim.result_ref),('CLAIMED',None))
            self.assertFalse(any(native.persistence.load_artifact(a).artifact_type=='document.inspection.safe_json'
                for a in native.persistence.artifacts_for_run(body['native_job_id'])))
        self.assertEqual(self.stats()['reserved'],0)
    def test_failure_evidence_tamper_refuses_dead_letter_finalization(self):
        run,worker,body,source=self.failed_cut();request=self.request(worker)
        with self.service.native(body) as native:
            evidence=native.persistence.load_artifact('evidence-'+body['native_job_id'][4:])
            native.cas._path(evidence.blob_digest).write_bytes(b'SYNTHETIC_CORRUPTION')
        self.assertNotEqual(self.recover(worker,request).status_code,200)
        with self.service.native(body) as native:
            self.assertEqual(native.queue.get('inspect-'+body['native_job_id'][4:]).state,'DELIVERED')
        self.assertEqual(self.stats()['reserved'],2)
def selected_suite():
    return unittest.defaultTestLoader.loadTestsFromTestCase(FailedTerminalRecovery)
if __name__=='__main__':unittest.TextTestRunner(verbosity=2).run(selected_suite())
