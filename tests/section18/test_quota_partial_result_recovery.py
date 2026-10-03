"""Genuine result publication, exhausted evidence CAS and real worker cuts."""
from pathlib import Path
import json,os,secrets,subprocess,sys,time,unittest
from unittest.mock import patch
from test_batch001 import Base,TestClient,create_app
from test_quota_terminal_recovery import QuotaTerminalRecovery
from test_worker_recovery import WorkerRecovery,RECOVER_CHILD
from apps.operator.contracts import Principal,PERMISSIONS
from apps.operator.service import Service
from bie.infrastructure.artifact_store import BlobRef

class QuotaPartialResultRecovery(Base):
    body=WorkerRecovery.body;stats=WorkerRecovery.stats
    request=WorkerRecovery.request;recover=WorkerRecovery.recover
    unchanged=QuotaTerminalRecovery.unchanged
    def cut(self,mode='dead_letter'):
        return QuotaTerminalRecovery.quota_cut(self,mode,reserve_result=True)
    def result_record(self,body):
        with self.service.native(body) as native:
            result=native.persistence.load_artifact('result-'+body['native_job_id'][4:])
            raw=native.cas.get_bytes(BlobRef(result.blob_algorithm,result.blob_digest,result.blob_size))
        return result,raw
    def assert_failed_only(self,run,body,used,raw):
        state=self.service.status(self.p,run)
        self.assertEqual((state['status'],state['queue_state'],state['result_available'],state['artifact_refs']),
                         ('FAILED','DEAD_LETTER',False,[]))
        self.assertEqual(self.result_record(body)[1],raw,'Retain authentic uncommitted result; do not delete or rewrite')
        self.assertEqual(self.service.cas_budget.inventory()['bytes'],used)
        self.assertEqual(self.service.failure(self.p,run)['evidence_refs'],[])
        with self.service.native(body) as native:
            claim=native.idempotency.get(body['native_key'])
            self.assertEqual((claim.state,claim.result_ref),('CLAIMED',None))
        self.assertEqual(self.stats()['reserved'],0)
    def test_real_result_then_evidence_quota_cut_preserves_failed_state_and_replays(self):
        run,worker,body,used=self.cut();_,raw=self.result_record(body);request=self.request(worker)
        with patch('apps.api.job_service.inspect_real_pdf_toc') as inspector:
            response=self.recover(worker,request)
        self.assertEqual(response.status_code,200,response.text);inspector.assert_not_called()
        self.assert_failed_only(run,body,used,raw)
        self.assertEqual(self.get('runs/'+run+'/result').status_code,409)
        events=self.stats()['events'];self.assertTrue(self.recover(worker,request).json()['replayed'])
        self.assertEqual(self.stats()['events'],events)
    def test_real_partial_result_before_blocked_recovers_after_service_and_app_restart(self):
        run,worker,body,used=self.cut('blocked');_,raw=self.result_record(body)
        self.client.close();self.service=Service(self.root,self.creds)
        self.client=TestClient(create_app(self.service),base_url='http://localhost',raise_server_exceptions=False)
        r=self.recover(worker,self.request(worker));self.assertEqual(r.status_code,200,r.text)
        self.assert_failed_only(run,body,used,raw)
    def test_corrupt_uncommitted_result_cannot_finalize_queue_or_release_credit(self):
        run,worker,body,_=self.cut();request=self.request(worker)
        with self.service.native(body) as native:
            result=native.persistence.load_artifact('result-'+body['native_job_id'][4:])
            native.cas._path(result.blob_digest).write_bytes(b'SYNTHETIC_CORRUPTION')
        self.assertNotEqual(self.recover(worker,request).status_code,200);self.unchanged(body)
    def test_foreign_source_metadata_cannot_finalize_even_when_blob_is_untouched(self):
        run,worker,body,_=self.cut();request=self.request(worker)
        with self.service.native(body) as native:
            with native.persistence._conn() as db:
                db.execute('UPDATE artifact_records SET metadata_json=? WHERE artifact_id=?',
                    (json.dumps({'source_hash':'0'*64}),'result-'+body['native_job_id'][4:]))
        self.assertNotEqual(self.recover(worker,request).status_code,200);self.unchanged(body)
    def test_foreign_tenant_and_revoked_principal_cannot_recover_partial_result(self):
        run,worker,body,_=self.cut();request=self.request(worker)
        token=secrets.token_hex(32);foreign=Principal('foreign','tenant-b',PERMISSIONS,time.time()+3600)
        self.creds.grant(token,foreign)
        r=self.client.post('/operator/v1/admin/workers/'+worker+'/reconcile',
            headers={'Authorization':'Bearer '+token},json=request)
        self.assertEqual(r.status_code,404);self.unchanged(body)
        self.creds.revoke(self.token)
        self.assertEqual(self.recover(worker,request).status_code,401);self.unchanged(body)
    def test_actual_competing_recovery_processes_settle_partial_result_once_at_capacity(self):
        run,worker,body,used=self.cut();_,raw=self.result_record(body);request=self.request(worker)
        source_root=Path(__file__).resolve().parents[2];release=self.root/'recovery-release'
        env={k:v for k,v in os.environ.items() if k in ('PATH','SystemRoot','TEMP','TMP','WINDIR')}
        env.update(PYTHONPATH=str(source_root),PYTHONUTF8='1',PYTHONDONTWRITEBYTECODE='1')
        children=[];before=self.stats()['events']
        try:
            for _ in range(2):
                children.append(subprocess.Popen([sys.executable,'-B','-c',RECOVER_CHILD,str(self.root),worker,
                    request['expected_record_sha256'],request['idempotency_key'],str(release)],cwd=source_root,env=env,
                    stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True))
            release.touch();rows=[]
            for child in children:
                out,err=child.communicate(timeout=25);self.assertEqual(child.returncode,0,err);rows.append(json.loads(out))
        finally:
            for child in children:
                if child.poll() is None:child.kill()
                child.wait(timeout=5);child.stdout.close();child.stderr.close()
        self.assertEqual(sorted(r['replayed'] for r in rows),[False,True])
        self.assertEqual(self.stats()['events'],before+1);self.assert_failed_only(run,body,used,raw)

def selected_suite():return unittest.defaultTestLoader.loadTestsFromTestCase(QuotaPartialResultRecovery)
if __name__=='__main__':unittest.main(verbosity=2)
