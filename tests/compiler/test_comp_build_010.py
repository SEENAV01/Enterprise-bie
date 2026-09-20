from dataclasses import asdict,replace
from hashlib import sha256
from pathlib import Path
import json
import tempfile
import unittest
from bie.compiler.build_common import BuildError
from bie.compiler.artifact_hashing import *

class TestBuild010(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        (self.root/'a.bin').write_bytes(b'abc');(self.root/'b.bin').write_bytes(b'def')
    def tearDown(self):self.tmp.cleanup()
    def manifest(self):return hash_artifacts(self.root,['b.bin','a.bin'],binding_sha256='a'*64)
    def test_sha256_known_bytes(self):self.assertEqual(hash_artifact(self.root,'a.bin').sha256,sha256(b'abc').hexdigest())
    def test_paths_sorted(self):self.assertEqual([a.path for a in self.manifest().artifacts],['a.bin','b.bin'])
    def test_manifest_deterministic(self):self.assertEqual(self.manifest(),self.manifest())
    def test_valid_verification(self):self.assertTrue(verify_artifacts(self.root,self.manifest()).passed)
    def test_same_size_tampering_detected(self):
        m=self.manifest();(self.root/'a.bin').write_bytes(b'xyz');self.assertFalse(verify_artifacts(self.root,m).passed)
    def test_missing_artifact_detected(self):
        m=self.manifest();(self.root/'a.bin').unlink();self.assertFalse(verify_artifacts(self.root,m).passed)
    def test_binding_tampering_detected(self):
        m=replace(self.manifest(),binding_sha256='b'*64);self.assertFalse(verify_artifacts(self.root,m).passed)
    def test_size_tampering_detected(self):
        m=self.manifest();m=replace(m,artifacts=(replace(m.artifacts[0],size_bytes=4),m.artifacts[1]))
        self.assertFalse(verify_artifacts(self.root,m).passed)
    def test_duplicate_paths_rejected(self):
        with self.assertRaises(BuildError):hash_artifacts(self.root,['a.bin','a.bin'],binding_sha256='a'*64)
    def test_empty_path_set_rejected(self):
        with self.assertRaises(BuildError):hash_artifacts(self.root,[],binding_sha256='a'*64)
    def test_empty_artifact_requires_explicit_permission(self):
        (self.root/'empty').write_bytes(b'')
        with self.assertRaises(BuildError):hash_artifact(self.root,'empty')
        self.assertEqual(hash_artifact(self.root,'empty',allow_empty=True).size_bytes,0)
    def test_symlink_file_rejected(self):
        (self.root/'s.bin').symlink_to(self.root/'a.bin')
        with self.assertRaises(BuildError):hash_artifact(self.root,'s.bin')
    def test_symlink_directory_rejected(self):
        (self.root/'d').symlink_to(self.root,target_is_directory=True)
        with self.assertRaises(BuildError):hash_artifact(self.root,'d/a.bin')
    def test_unsafe_paths_rejected(self):
        for path in ('../a.bin','/etc/passwd','a/../b','a\\b','C:/x','./a','a//b','a\nx'):
            with self.subTest(path=path),self.assertRaises(BuildError):hash_artifact(self.root,path)
    def test_relocation_preserves_manifest(self):
        with tempfile.TemporaryDirectory() as td:
            other=Path(td);(other/'a.bin').write_bytes(b'abc');(other/'b.bin').write_bytes(b'def')
            self.assertTrue(verify_artifacts(other,self.manifest()).passed)
    def test_acceptance_cannot_be_promoted(self):
        m=replace(self.manifest(),accepted=True);self.assertFalse(verify_artifacts(self.root,m).passed)
    def test_roundtrip_manifest(self):self.assertEqual(manifest_from_dict(asdict(self.manifest())),self.manifest())
    def test_unknown_schema_rejected(self):self.assertFalse(verify_artifacts(self.root,replace(self.manifest(),schema_version='x')).passed)
    def test_nan_canonical_json_rejected(self):
        with self.assertRaises(BuildError):canonical_json({'x':float('nan')})
