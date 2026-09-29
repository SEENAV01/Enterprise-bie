from h7_helpers import *
import sqlite3
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'qa_publication22'))
from pub22_support import Fixture,NOW as PUB_NOW

class Publication(Temp):
    def setUp(self):
        super().setUp();self.f=Fixture(self.root/'candidate');self.cert=self.f.issue();self.approvals=self.f.approvals();self.store=PublicationStore(self.root/'store',create=True)
    def publish(self,cert=None,expected_head=None):
        f=self.f
        return self.store.publish(f.request,f.root,f.policy,self.approvals,f.authorities,f.journal,cert or self.cert,now=PUB_NOW,verifier=f.verifier,expected_head=expected_head)
    def serve(self,artifact='source',now=PUB_NOW):
        f=self.f
        return self.store.serve(f.request.release_id,artifact,f.request,f.policy,self.approvals,f.authorities,f.journal,now=now,verifier=f.verifier)
    def test_actual_verified_roundtrip(self):
        r=self.publish();self.assertEqual(r['status'],'LOCAL_PUBLISHED');self.assertFalse(r['production_authorized']);self.assertFalse(r['product_accepted'])
        self.assertEqual(self.serve(),b'SYNTHETIC original; not a textbook')
    def test_diagnostic_certificate_not_promoted(self):
        self.assertEqual(self.cert['status'],'DIAGNOSTIC_ONLY');self.publish();self.assertFalse(self.cert['release_authorized'])
    def test_original_mutation_after_publish_does_not_change_served_bytes(self):
        self.publish();(self.f.root/'subjects/source.txt').write_text('MUTATED AFTER PUBLICATION')
        self.assertEqual(self.serve(),b'SYNTHETIC original; not a textbook')
    def test_original_mutation_before_publish_blocks(self):
        (self.f.root/'subjects/source.txt').write_text('MUTATED BEFORE PUBLICATION')
        with self.assertRaises(ContractError):self.publish()
        self.error('H7_RELEASE_NOT_ACTIVE',self.serve)
    def test_idempotent_retry(self):
        a=self.publish();b=self.publish();self.assertEqual(b['status'],'ALREADY_PUBLISHED');self.assertEqual(a['capsule_sha256'],b['capsule_sha256'])
        with sqlite3.connect(self.store.db) as c:self.assertEqual(c.execute('select count(*) from audit').fetchone()[0],1)
    def test_reopen(self):
        self.publish();self.store=PublicationStore(self.root/'store');self.assertEqual(self.serve(),b'SYNTHETIC original; not a textbook')
    def test_expiry_at_serving(self):
        self.publish();self.error('CERTIFICATE_TIME',self.serve,now=self.cert['expires_at'])
    def test_revocation_at_serving(self):
        self.publish();self.f.journal.revoke(self.cert,reason='SYNTHETIC-REVOKE',as_of=PUB_NOW+1)
        with self.assertRaises(ContractError):self.serve(now=PUB_NOW+2)
    def test_corrupt_certificate(self):
        self.error('CERTIFICATE_SIGNATURE',self.publish,{**self.cert,'signature':'0'*64})
    def test_wrong_head(self):self.error('H7_ACTIVATION_CONFLICT',self.publish,expected_head='0'*64)
    def test_deactivation(self):
        p=self.publish();self.store.deactivate(self.f.request.release_id,expected_head=p['capsule_sha256'],reason='withdraw',now=PUB_NOW+1)
        self.error('H7_RELEASE_NOT_ACTIVE',self.serve)
    def test_deactivation_compare_and_swap(self):
        self.publish();self.error('H7_ACTIVATION_CONFLICT',self.store.deactivate,self.f.request.release_id,expected_head='0'*64,reason='wrong head',now=PUB_NOW)
        self.assertTrue(self.serve())
    def test_orphan_blob_is_not_a_release(self):
        self.store.put(b'PREPARED THEN PROCESS STOPPED');self.store=PublicationStore(self.root/'store')
        self.error('H7_RELEASE_NOT_ACTIVE',self.serve)
    def test_changed_blob_blocks_serving(self):
        self.publish();r=self.f.request.bundle.candidate.artifacts[0];p=self.store.blobs/r.sha256;p.chmod(0o600);p.write_bytes(b'changed')
        self.error('H7_BLOB_CORRUPTION',self.serve)
    def test_missing_blob(self):
        self.publish();r=self.f.request.bundle.candidate.artifacts[0];(self.store.blobs/r.sha256).unlink()
        with self.assertRaises(ContractError):self.serve()
    def test_blob_not_hardlinked_from_input(self):
        self.publish();r=self.f.request.bundle.candidate.artifacts[0]
        self.assertNotEqual((self.f.root/r.path).stat().st_ino,(self.store.blobs/r.sha256).stat().st_ino)
        self.assertEqual((self.store.blobs/r.sha256).stat().st_nlink,1)
    def test_unknown_artifact(self):
        self.publish();self.error('H7_ARTIFACT_NOT_IN_RELEASE',self.serve,'missing-artifact')
    def test_capsule_corruption(self):
        self.publish()
        with sqlite3.connect(self.store.db) as c:c.execute("UPDATE releases SET capsule='{}'")
        self.error('H7_CAPSULE_CORRUPTION',self.serve)
    def test_audit_corruption(self):
        self.publish()
        with sqlite3.connect(self.store.db) as c:c.execute("UPDATE audit SET body='{}'")
        self.error('H7_STORE_AUDIT_CORRUPT',PublicationStore,self.store.path)
    def test_shared_directory_rejected(self):
        (self.root/'public-store').mkdir(mode=0o755);self.error('H7_STORE_PRIVATE',PublicationStore,self.root/'public-store')
    def test_uninitialized_rejected(self):
        (self.root/'private').mkdir(mode=0o700);self.error('H7_STORE_NOT_INITIALIZED',PublicationStore,self.root/'private')
    def test_store_link_rejected(self):
        (self.root/'alias').symlink_to(self.store.path);self.error('H7_LINKED_ROOT',PublicationStore,self.root/'alias')
    def test_blob_symlink_rejected(self):
        data=b'attack';h=identity(data);(self.root/'other').write_bytes(data);(self.store.blobs/h).symlink_to(self.root/'other')
        with self.assertRaises(ContractError):self.store.put(data)
    def test_store_create_no_overwrite(self):
        with self.assertRaises(FileExistsError):PublicationStore(self.store.path,create=True)
