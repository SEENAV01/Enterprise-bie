"""Real exhausted CAS + process cut; no invented terminal receipt or result."""
from pathlib import Path
import os,subprocess,sys,unittest
from unittest.mock import patch
from test_batch001 import Base,DATA,TestClient,create_app
from apps.operator.service import Service
from apps.operator.cas_budget import CASLimits
from test_failed_terminal_recovery import CHILD
from test_worker_recovery import WorkerRecovery

class QuotaTerminalRecovery(Base):
    body=WorkerRecovery.body;stats=WorkerRecovery.stats
    request=WorkerRecovery.request;recover=WorkerRecovery.recover
    def quota_cut(self,mode='dead_letter',reserve_result=False):
        self.make_run();admission=self.service.cas_budget.inventory()['bytes'];used=admission
        if reserve_result:
            from apps.operator.contracts import canonical
            from bie.document_intelligence.real_pdf_toc_runtime import inspect_real_pdf_toc
            used+=len(canonical(inspect_real_pdf_toc(DATA).to_safe_dict()))
        root=self.root/'quota-root';limited=Service(root,self.creds,cas_limits=CASLimits(max_bytes=used))
        source=limited.import_pdf(self.p,DATA)
        run=limited.create(self.p,source['source_id'],{},'test-run')['run_id']
        self.assertEqual(limited.cas_budget.inventory()['bytes'],admission)
        self.client.close();self.service=limited;self.root=root
        self.client=TestClient(create_app(limited),base_url='http://localhost',raise_server_exceptions=False)
        source_root=Path(__file__).resolve().parents[2]
        env={k:v for k,v in os.environ.items() if k in ('PATH','SystemRoot','TEMP','TMP','WINDIR')}
        env.update(PYTHONPATH=str(source_root),PYTHONUTF8='1',PYTHONDONTWRITEBYTECODE='1')
        child=subprocess.Popen([sys.executable,'-B','-c',CHILD,str(root),run,mode],cwd=source_root,env=env,
            stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        try:
            out,err=child.communicate(timeout=25);self.assertEqual(child.returncode,81,err);worker=out.strip()
        finally:
            if child.poll() is None:child.kill()
            child.wait(timeout=5);child.stdout.close();child.stderr.close()
        with limited.catalog.tx(read_only=True) as db:_,body=limited.catalog.intent(db,self.p,run)
        with limited.native(body) as native:
            attempt=native.persistence.load_run_state(body['native_job_id'])['stages']['PDF_INSPECTION']['attempts'][0]
            self.assertEqual((attempt['state'],attempt['diagnostics'],attempt['output_artifact_refs'],attempt['evidence_refs']),
                             ('FAILED',['cas_capacity_reached'],[],[]))
            self.assertEqual(native.queue.get('inspect-'+body['native_job_id'][4:]).state,'DELIVERED')
            records=native.persistence.artifacts_for_run(body['native_job_id'])
            self.assertEqual('result-'+body['native_job_id'][4:] in records,reserve_result)
            self.assertNotIn('evidence-'+body['native_job_id'][4:],records)
        self.assertEqual(limited.cas_budget.inventory()['bytes'],used)
        self.assertEqual(self.get('runs/'+run).status_code,409)
        return run,worker,body,used
    def unchanged(self,body):
        with self.service.native(body) as native:
            self.assertEqual(native.queue.get('inspect-'+body['native_job_id'][4:]).state,'DELIVERED')
        self.assertEqual(self.stats()['reserved'],2)
    def test_real_quota_cut_reconciles_failure_without_fake_evidence_and_replays_at_capacity(self):
        run,worker,body,used=self.quota_cut();request=self.request(worker)
        with patch('apps.api.job_service.inspect_real_pdf_toc') as inspector:
            response=self.recover(worker,request)
        self.assertEqual(response.status_code,200,response.text);inspector.assert_not_called()
        state=self.service.status(self.p,run)
        self.assertEqual((state['status'],state['queue_state'],state['result_available']),('FAILED','DEAD_LETTER',False))
        self.assertEqual(self.service.failure(self.p,run)['evidence_refs'],[])
        self.assertEqual(self.service.cas_budget.inventory()['bytes'],used)
        self.assertEqual(self.stats()['reserved'],0);events=self.stats()['events']
        self.assertTrue(self.recover(worker,request).json()['replayed'])
        self.assertEqual(self.stats()['events'],events)
    def test_real_quota_cut_before_blocked_survives_fresh_service_restart(self):
        run,worker,body,used=self.quota_cut('blocked')
        self.service=Service(self.root,self.creds)
        self.client.close();self.client=TestClient(create_app(self.service),base_url='http://localhost',raise_server_exceptions=False)
        r=self.recover(worker,self.request(worker));self.assertEqual(r.status_code,200,r.text)
        state=self.service.status(self.p,run)
        self.assertEqual((state['engine_run_state'],state['status'],state['queue_state']),('BLOCKED','FAILED','DEAD_LETTER'))
        with self.service.native(body) as native:
            claim=native.idempotency.get(body['native_key'])
            self.assertEqual((claim.state,claim.result_ref),('CLAIMED',None))
        self.assertEqual(self.service.cas_budget.inventory()['bytes'],used)
    def test_quota_source_corruption_cannot_be_finalized(self):
        run,worker,body,_=self.quota_cut();request=self.request(worker)
        with self.service.native(body) as native:
            source=native.persistence.load_artifact('source-'+body['native_job_id'][4:])
            native.cas._path(source.blob_digest).write_bytes(b'SYNTHETIC_TAMPER')
        self.assertNotEqual(self.recover(worker,request).status_code,200);self.unchanged(body)
    def test_quota_policy_tamper_cannot_be_finalized(self):
        run,worker,body,_=self.quota_cut();request=self.request(worker)
        self.service.cas_budget.policy_path.write_bytes(b'{}')
        self.assertNotEqual(self.recover(worker,request).status_code,200);self.unchanged(body)
    def test_quota_foreign_claim_owner_cannot_be_finalized(self):
        run,worker,body,_=self.quota_cut();request=self.request(worker)
        with self.service.native(body) as native:
            with native.idempotency.db:
                native.idempotency.db.execute('UPDATE claims SET owner=? WHERE key=?',('foreign-owner',body['native_key']))
        self.assertNotEqual(self.recover(worker,request).status_code,200);self.unchanged(body)

def selected_suite():return unittest.defaultTestLoader.loadTestsFromTestCase(QuotaTerminalRecovery)
if __name__=='__main__':unittest.main(verbosity=2)
