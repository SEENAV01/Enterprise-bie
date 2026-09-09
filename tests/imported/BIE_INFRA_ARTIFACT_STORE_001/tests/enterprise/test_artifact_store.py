import unittest, tempfile
from pathlib import Path
from enterprise.artifact_store import *

class StoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.cas=FileSystemCAS(Path(self.tmp.name))
        self.cat=ArtifactCatalog(self.cas)
    def tearDown(self):self.tmp.cleanup()

    def test_same_bytes_deduplicate(self):
        a=self.cas.put_bytes(b"hello");b=self.cas.put_bytes(b"hello")
        self.assertEqual(a,b)

    def test_roundtrip_integrity(self):
        ref=self.cas.put_bytes(b"abc")
        self.assertEqual(self.cas.get_bytes(ref),b"abc")

    def test_corruption_detected(self):
        ref=self.cas.put_bytes(b"abc")
        self.cas._path(ref.digest).write_bytes(b"bad")
        with self.assertRaises(ArtifactStoreError):self.cas.get_bytes(ref)

    def test_register_requires_existing_blob(self):
        fake=BlobRef("sha256","0"*64,3)
        r=ArtifactRecord("a","x",fake,"run","S")
        with self.assertRaises(ArtifactStoreError):self.cat.register(r)

    def test_parent_must_exist(self):
        with self.assertRaises(ArtifactStoreError):
            self.cat.put_artifact("child","x",b"x","r","B",["missing"])

    def test_lineage_and_indexes(self):
        self.cat.put_artifact("src","source",b"s","r","SOURCE")
        self.cat.put_artifact("reason","reasoning",b"r","r","REASONING",["src"])
        self.cat.put_artifact("scene","scene.ir",b"z","r","SCENE_IR",["reason"])
        self.assertEqual(self.cat.trace_to_roots("scene"),{"src"})
        self.assertEqual([x.artifact_id for x in self.cat.parents_of("scene")],["reason"])
        self.assertEqual([x.artifact_id for x in self.cat.children_of("src")],["reason"])
        self.assertEqual(len(self.cat.artifacts_for_run("r")),3)

    def test_evidence_first_class(self):
        self.cat.put_artifact("src","source",b"s","r","SOURCE")
        self.cat.put_artifact("ev","qa.evidence",b"pass","r","QA",["src"],evidence=True)
        self.assertEqual([x.artifact_id for x in self.cat.evidence_for_run("r")],["ev"])

    def test_conflicting_reregistration_rejected(self):
        self.cat.put_artifact("a","x",b"one","r","S")
        with self.assertRaises(ArtifactStoreError):
            self.cat.put_artifact("a","x",b"two","r","S")

    def test_idempotent_same_registration_allowed(self):
        r=self.cat.put_artifact("a","x",b"one","r","S")
        self.cat.register(r)
        self.assertEqual(self.cat.read_artifact("a"),b"one")

    def test_verify_all(self):
        r=self.cat.put_artifact("a","x",b"one","r","S")
        self.assertEqual(self.cat.verify_all(),[])
        self.cas._path(r.blob.digest).write_bytes(b"corrupt")
        self.assertEqual(self.cat.verify_all(),["a"])

if __name__=="__main__":unittest.main()
