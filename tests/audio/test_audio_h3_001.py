import hashlib,importlib,json,uuid
from dataclasses import replace
from pathlib import Path
from bie.audio.common import AudioError,fingerprint
from bie.audio.durable_contract import *
from .durable_test_support import DurableCase,RUN_ID,KEY_ID,clone,rehash

class CanonicalRequestTests(DurableCase):
    def test_exact_pinned_canonical_dependency_bytes(self):
        root=Path(__file__).resolve().parents[2]
        m=json.loads((root/'docs/evidence/audio-integration-001/CANONICAL_DEPENDENCY_BINDING.json').read_text())
        rows=[x for x in m['files'] if x['group']=='durable_canonical'];self.assertEqual(len(rows),5)
        for row in rows:
            mod=importlib.import_module(row['path'][:-3].replace('/','.'))
            b=Path(mod.__file__).read_bytes()
            self.assertEqual(hashlib.sha256(b).hexdigest(),row['sha256'])
            self.assertEqual(hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest(),row['expected_git_blob'])
    def test_canonical_catalog_not_recreated(self):
        from bie.audio.durable_store import SQLiteArtifactCatalog
        from bie.director.director_durable_recovery import SQLiteArtifactCatalog as C
        self.assertIs(SQLiteArtifactCatalog,C)
    def test_canonical_lease_class_not_recreated(self):
        from bie.audio.durable_jobs import DirectorLeaseStore
        from bie.director.director_durable_recovery import DirectorLeaseStore as C
        self.assertIs(DirectorLeaseStore,C)
    def test_request_binds_exact_wav(self):self.assertEqual(validate_request(self.request,self.mix.wav_bytes),self.policy)
    def test_invalid_run_uuid(self):
        with self.assertRaises(AudioError):build_request(self.job,run_id='not-uuid',job_id='j',revision='1',runtime_fingerprint=self.runtime['fingerprint'],key_id=KEY_ID)
    def test_boolean_policy_blocked(self):
        with self.assertRaises(AudioError):DurablePolicy(max_attempts=True)
    def test_heartbeat_margin_required(self):
        with self.assertRaises(AudioError):DurablePolicy(lease_ttl_seconds=10,heartbeat_seconds=5)
    def test_budget_policy_consistency(self):
        with self.assertRaises(AudioError):DurablePolicy(max_store_bytes=1_000_000)
    def test_changed_revision_new_key(self):
        r=build_request(self.job,run_id=RUN_ID,job_id='scene-1',revision='2',runtime_fingerprint=self.runtime['fingerprint'],key_id=KEY_ID)
        self.assertNotEqual(request_key(r),request_key(self.request))
    def test_same_job_revision_different_source_same_key_but_new_fingerprint(self):
        j=clone(self.job);j['segments'][0]['voice_fingerprint']=fingerprint('different-voice');rehash(j)
        r=build_request(j,run_id=RUN_ID,job_id='scene-1',revision='1',runtime_fingerprint=self.runtime['fingerprint'],key_id=KEY_ID)
        self.assertEqual(request_key(r),request_key(self.request));self.assertNotEqual(r['fingerprint'],self.request['fingerprint'])
    def test_cross_run_new_key(self):
        r=build_request(self.job,run_id=str(uuid.uuid4()),job_id='scene-1',revision='1',runtime_fingerprint=self.runtime['fingerprint'],key_id=KEY_ID)
        self.assertNotEqual(request_key(r),request_key(self.request))
    def test_request_mutation_rehash_cannot_change_code_identity(self):
        r=clone(self.request);r['implementation']=fingerprint('other');rehash(r)
        with self.assertRaises(AudioError):validate_request(r)
    def test_no_product_acceptance(self):
        r=clone(self.request);r['product_accepted']=True;rehash(r)
        with self.assertRaises(AudioError):validate_request(r)
    def test_extra_request_field(self):
        r=clone(self.request);r['extra']=1;rehash(r)
        with self.assertRaises(AudioError):validate_request(r)
    def test_original_source_not_mutated(self):
        self.assertEqual(self.request['job'],self.job);self.request['job']['segments'][0]['spoken_text']='changed'
        self.assertNotEqual(self.request['job'],self.job)
    def test_wrong_wav_rejected_before_storage(self):
        with self.assertRaises(AudioError):validate_request(self.request,b'bad')
    def test_signer_binding_changes_request(self):
        r=build_request(self.job,run_id=RUN_ID,job_id='scene-1',revision='1',runtime_fingerprint=self.runtime['fingerprint'],key_id='other')
        self.assertNotEqual(r['fingerprint'],self.request['fingerprint'])
