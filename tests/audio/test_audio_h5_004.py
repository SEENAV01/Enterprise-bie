import concurrent.futures,json,tempfile,time,unittest
from pathlib import Path
from unittest.mock import patch
from bie.audio.common import AudioError
from bie.audio.acoustic_contract import canonical
from bie.audio.pipeline_contract import request_key
from bie.audio.pipeline_durable import PipelineCoordinator,PipelineArtifactStore,execute_durable
from bie.director.director_durable_recovery import DirectorLeaseStore,RecoveryError
from .pipeline_test_support import context,actual,clone,request,store_actual

class Durable(unittest.TestCase):
    def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.c=context()
    def tearDown(self):self.tmp.cleanup()
    def test_01_actual_bundle_cas_roundtrip(self):
        store,ref,jobs=store_actual(self.root);v=store.load(ref,self.c['request'],self.c['trust']);self.assertEqual(v['files'],actual()[0])
    def test_02_cold_store_instance_reopens(self):
        store,ref,_=store_actual(self.root);second=PipelineArtifactStore(self.root/'artifacts',profile=self.c['profile'])
        self.assertEqual(second.load(ref,self.c['request'],self.c['trust'])['artifact_ref'],ref)
    def test_03_completed_run_reuse_has_no_native_call(self):
        store,ref,jobs=store_actual(self.root);r=self.c['request'];t=jobs.acquire(r);jobs.complete(t,canonical(ref).decode(),store,r,self.c['trust'])
        with patch('bie.audio.pipeline_durable.issue_execution',side_effect=AssertionError('must not resynthesize')):
            out=execute_durable(r,self.c['profile'],self.c['trust'],self.c['key'],root=self.root)
        self.assertTrue(out['cache_hit']);self.assertEqual(out['native_pipeline_runs'],0);self.assertEqual(out['files'],actual()[0])
    def test_04_revocation_blocks_stored_reuse(self):
        store,ref,_=store_actual(self.root);trust=clone(self.c['trust']);trust['issuers'][0]['revoked']=True
        with self.assertRaises(AudioError):store.load(ref,self.c['request'],trust)
    def test_05_changed_job_revision_not_accepted_for_ref(self):
        store,ref,_=store_actual(self.root)
        with self.assertRaises(AudioError):store.load(ref,request(revision='new'),self.c['trust'])
    def test_06_same_job_input_conflict(self):
        jobs=PipelineCoordinator(self.root/'jobs');jobs.acquire(self.c['request'])
        raw=clone(self.c['source']);raw['drafts'][0]['text']='An altered source.'
        with self.assertRaises(RecoveryError):jobs.acquire(request(source=raw))
    def test_07_live_duplicate_rejected(self):
        jobs=PipelineCoordinator(self.root/'jobs');jobs.acquire(self.c['request'])
        with self.assertRaises(RecoveryError):jobs.acquire(self.c['request'])
    def test_08_expired_owner_cannot_heartbeat(self):
        jobs=PipelineCoordinator(self.root/'jobs');now=time.time();old=jobs.acquire(self.c['request'],now=now)
        newer=jobs.acquire(self.c['request'],now=now+31);self.assertEqual(newer.lease.epoch,2)
        with self.assertRaises(RecoveryError):jobs.heartbeat(old,now=now+31)
    def test_09_expired_owner_cannot_complete(self):
        store,ref,jobs=store_actual(self.root);now=time.time();old=jobs.acquire(self.c['request'],now=now)
        jobs.acquire(self.c['request'],now=now+31)
        with self.assertRaises(RecoveryError):jobs.complete(old,canonical(ref).decode(),store,self.c['request'],self.c['trust'],now=now+31)
    def test_10_attempt_limit(self):
        jobs=PipelineCoordinator(self.root/'jobs');now=time.time()
        for i in range(3):jobs.acquire(self.c['request'],now=now+31*i)
        with self.assertRaises(AudioError):jobs.acquire(self.c['request'],now=now+93)
    def test_11_claim_complete_lease_incomplete_recovery(self):
        store,ref,jobs=store_actual(self.root);now=time.time();r=self.c['request'];t=jobs.acquire(r,now=now);encoded=canonical(ref).decode()
        with patch.object(DirectorLeaseStore,'complete',side_effect=RuntimeError('injected crash after claim commit')):
            with self.assertRaises(RuntimeError):jobs.complete(t,encoded,store,r,self.c['trust'],now=now)
        self.assertEqual(jobs.state(r)['claim_state'],'COMPLETED');self.assertEqual(jobs.state(r)['lease_state'],'ACTIVE')
        recovered=jobs.acquire(r,now=now+31);self.assertEqual(recovered.claimed_result_ref,encoded)
        result=jobs.complete(recovered,encoded,store,r,self.c['trust'],now=now+31)
        self.assertEqual(result['files'],actual()[0]);self.assertEqual(jobs.state(r)['lease_state'],'COMPLETED')
    def test_12_concurrent_acquire_one_live_owner(self):
        def attempt(_):
            j=PipelineCoordinator(self.root/'jobs')
            try:j.acquire(self.c['request']);return 'owned'
            except RecoveryError:return 'blocked'
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:out=list(pool.map(attempt,range(2)))
        self.assertEqual(sorted(out),['blocked','owned'])
    def test_13_wrong_ticket_request(self):
        store,ref,jobs=store_actual(self.root);t=jobs.acquire(self.c['request'])
        with self.assertRaises(AudioError):jobs.complete(t,canonical(ref).decode(),store,request(job_id='other'),self.c['trust'])
    def test_14_namespace_separate_from_acoustic(self):
        self.assertTrue(request_key(self.c['request']).startswith('AUDIO:LOCAL-PIPELINE:'))
    def test_15_tampered_catalog_blob(self):
        store,ref,_=store_actual(self.root)
        with store.base.session() as io:
            env=io.load(__import__('bie.director.director_artifacts',fromlist=['reference']).reference(ref));blob=env.payload['blobs']['master.wav']
        from bie.infrastructure.artifact_store import BlobRef
        # Corrupt the actual CAS media bytes, not a test double.
        data=actual()[0]['master.wav'];matches=[p for p in (self.root/'artifacts/cas').rglob('*') if p.is_file() and p.stat().st_size==len(data) and p.read_bytes()==data]
        self.assertEqual(len(matches),1);matches[0].write_bytes(data[:-1]+bytes([data[-1]^1]))
        with self.assertRaises((ValueError,RuntimeError)):store.load(ref,self.c['request'],self.c['trust'])
    def test_16_same_actual_receipt_idempotent_put(self):
        store,ref,_=store_actual(self.root);f,r=actual();again=store.put(self.c['request'],f,r,self.c['trust']);self.assertEqual(ref,again)
    def test_17_artifact_parent_provenance(self):
        store,ref,_=store_actual(self.root)
        from bie.director.director_artifacts import reference
        with store.base.session() as io:
            graph=io.load_graph([reference(ref)])
            self.assertEqual(len(graph),3)
            self.assertEqual({e.artifact_type for e in graph.values()},{'source.asset','audio.pipeline.request','audio.pipeline.execution'})
            self.assertTrue(all(e.provenance_summary.sources for e in graph.values()))
    def test_18_pre_cancel_no_store_completion(self):
        from threading import Event
        e=Event();e.set()
        with self.assertRaises(AudioError):execute_durable(self.c['request'],self.c['profile'],self.c['trust'],self.c['key'],root=self.root,cancellation=e)
        self.assertFalse((self.root/'jobs').exists())
    def test_19_expiry_exact_boundary_blocked(self):
        jobs=PipelineCoordinator(self.root/'jobs');now=time.time();t=jobs.acquire(self.c['request'],now=now)
        with self.assertRaises(AudioError):jobs.heartbeat(t,now=t.lease.expires_at)
