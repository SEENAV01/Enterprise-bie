import os,json,uuid
from pathlib import Path
from bie.audio.common import AudioError,fingerprint
from bie.audio.durable_store import *
from bie.audio.durable_contract import build_request,DurablePolicy
from .durable_test_support import *

class DurableArtifactTests(DurableCase):
    def test_put_reload_current_signature(self):
        ref=self.put();r=self.store.load(ref,self.request,self.trust,now=NOW)
        self.assertTrue(r['signature_reverified']);self.assertEqual(r['assessment']['status'],'REVIEW')
    def test_reopen_rebuilds_actual_sqlite_index(self):
        ref=self.put();reopened=AudioArtifactStore(self.root/'artifacts')
        self.assertEqual(reopened.inspect()['artifacts'],3)
        self.assertEqual(reopened.load(ref,self.request,self.trust,now=NOW)['media_sha256'],self.job['binding']['media_sha256'])
    def test_put_same_receipt_is_idempotent(self):
        self.assertEqual(self.put(),self.put());self.assertEqual(self.store.inspect()['artifacts'],3)
    def test_exact_waveform_in_canonical_cas(self):
        self.put();digest=self.job['binding']['media_sha256'];p=self.store.root/'cas/blobs/sha256'/digest[:2]/digest
        self.assertEqual(p.read_bytes(),self.mix.wav_bytes)
    def test_tampered_waveform_blocks_reload(self):
        ref=self.put();h=self.job['binding']['media_sha256'];p=self.store.root/'cas/blobs/sha256'/h[:2]/h;p.write_bytes(b'bad')
        with self.assertRaises(ValueError):self.store.load(ref,self.request,self.trust,now=NOW)
    def test_missing_waveform_blocks_reload(self):
        ref=self.put();h=self.job['binding']['media_sha256'];(self.store.root/'cas/blobs/sha256'/h[:2]/h).unlink()
        with self.assertRaises(ValueError):self.store.load(ref,self.request,self.trust,now=NOW)
    def test_signature_tamper_rehash_not_authority(self):
        rec=clone(self.signed);rec['payload']['issued_at']+=1
        with self.assertRaises(AudioError):self.store.put(self.request,self.mix.wav_bytes,rec,self.trust,now=NOW)
    def test_revocation_applies_to_stored_receipt(self):
        ref=self.put();trust=clone(self.trust);trust['issuers'][0]['revoked']=True
        with self.assertRaisesRegex(AudioError,'REVOKED'):self.store.load(ref,self.request,trust,now=NOW)
    def test_expiry_applies_to_stored_receipt(self):
        ref=self.put()
        with self.assertRaisesRegex(AudioError,'EXPIRED'):self.store.load(ref,self.request,self.trust,now=NOW+601)
    def test_new_trust_revision_reauthenticates(self):
        ref=self.put();trust=clone(self.trust);trust['revision']='another-policy'
        r=self.store.load(ref,self.request,trust,now=NOW)
        self.assertEqual(r['current_trust_fingerprint'],fingerprint(trust))
        self.assertEqual(r['assessment']['trust_fingerprint'],fingerprint(trust))
    def test_unknown_issuer_cannot_load(self):
        ref=self.put();trust=clone(self.trust);trust['issuers'][0]['key_id']='other'
        with self.assertRaisesRegex(AudioError,'UNKNOWN'):self.store.load(ref,self.request,trust,now=NOW)
    def test_request_from_other_run_blocked(self):
        ref=self.put();r=build_request(self.job,run_id=str(uuid.uuid4()),job_id='scene-1',revision='1',runtime_fingerprint=self.runtime['fingerprint'],key_id=KEY_ID)
        with self.assertRaises(AudioError):self.store.load(ref,r,self.trust,now=NOW)
    def test_wrong_artifact_ref_hash(self):
        ref=self.put();ref['content_hash']='0'*64
        with self.assertRaises(ValueError):self.store.load(ref,self.request,self.trust,now=NOW)
    def test_metadata_never_claims_source_document(self):
        self.put()
        with self.store.session() as io:
            roots=[io.load(r.artifact_id) for r in io.catalog.records.values() if not r.parent_artifact_ids]
            self.assertEqual(len(roots),1);self.assertEqual(roots[0].artifact_type,'source.asset')
            self.assertEqual(roots[0].payload['source_authority'],'DECLARED_SOURCE_REFS_NOT_DIR_ACCEPTANCE')
    def test_provenance_parent_chain_preserved(self):
        ref=self.put()
        with self.store.session() as io:
            graph=io.load_graph([reference(ref)]);self.assertEqual(len(graph),3)
            self.assertTrue(all(a.provenance_summary.sources for a in graph.values()))
    def test_no_private_signer_bytes_persisted(self):
        self.put()
        from cryptography.hazmat.primitives.serialization import Encoding,PrivateFormat,NoEncryption
        raw=self.signer.private_bytes(Encoding.Raw,PrivateFormat.Raw,NoEncryption())
        for p in self.store.root.rglob('*'):
            if p.is_file():self.assertNotIn(raw,p.read_bytes())
    def test_unsafe_root_rejected(self):
        p=self.root/'bad';p.mkdir(mode=0o777);p.chmod(0o777)
        with self.assertRaises(AudioError):AudioArtifactStore(p)
    def test_symlink_root_rejected(self):
        p=self.root/'link';p.symlink_to(self.store.root,target_is_directory=True)
        with self.assertRaises(AudioError):AudioArtifactStore(p)
    def test_symlink_child_rejected(self):
        (self.store.root/'bad').symlink_to('/tmp')
        with self.assertRaises(AudioError):self.put()
    def test_hardlinked_storage_rejected(self):
        p=self.store.root/'x';p.write_bytes(b'x');os.link(p,self.store.root/'y')
        with self.assertRaises(AudioError):self.put()
    def test_artifact_budget_fail_closed(self):
        policy=DurablePolicy(max_artifact_bytes=1024);store=AudioArtifactStore(self.root/'small',policy=policy)
        req=build_request(self.job,run_id=RUN_ID,job_id='j',revision='1',runtime_fingerprint=self.runtime['fingerprint'],key_id=KEY_ID,policy=policy)
        with self.assertRaisesRegex(AudioError,'BUDGET'):store.put(req,self.mix.wav_bytes,self.signed,self.trust,now=NOW)
    def test_rehashed_receipt_not_written(self):
        rec=clone(self.signed);rec['signature_ed25519_hex']='0'*128
        with self.assertRaises(AudioError):self.store.put(self.request,self.mix.wav_bytes,rec,self.trust,now=NOW)
        self.assertFalse((self.store.root/'artifacts.sqlite').exists())

    def test_inspect_detects_raw_media_corruption_not_only_envelope(self):
        self.put();h=self.job['binding']['media_sha256'];p=self.store.root/'cas/blobs/sha256'/h[:2]/h;p.write_bytes(b'tampered')
        with self.assertRaises(ValueError):self.store.inspect()
    def test_inspect_verifies_actual_media_blob(self):
        self.put();report=self.store.inspect();self.assertEqual(report['media_blobs_verified'],1)
        self.assertIn('not current issuer authentication',report['scope'])
