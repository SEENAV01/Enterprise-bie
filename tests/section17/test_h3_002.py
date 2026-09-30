import unittest,tempfile,shutil,json,hashlib,os
from pathlib import Path
from copy import deepcopy
from dataclasses import asdict,replace
from unittest.mock import patch
from bie.evaluation.benchmarks.models import BenchmarkError,digest,canonical_json
from bie.evaluation.benchmarks.adoption.contracts import *
from h3_support import fixture,measure,measured,rater,context,TD,LIMITS,ROOT,media,sha,policy,report,CONTRACT

from bie.evaluation.benchmarks.adoption.custody import *
class ConfinedCustodyTests(unittest.TestCase):
    def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.data=b'content';(self.root/'media').write_bytes(self.data);self.row={'path':'media','sha256':hashlib.sha256(self.data).hexdigest(),'size_bytes':len(self.data)}
    def tearDown(self):self.tmp.cleanup()
    def test_regular_file_capture(self):
        with open_root(self.root) as fd:self.assertEqual(self.row,capture(fd,self.row,maximum=100))
    def test_unsafe_relative_path_variants(self):
        for p in ('/abs','../x','a/../b','a//b','C:/x','a\\b','x\n','a/./b'):
            with self.subTest(path=p),self.assertRaises(BenchmarkError):relative_path(p)
    def test_symlink_file_rejected(self):
        (self.root/'link').symlink_to(self.root/'media');self.row['path']='link'
        with open_root(self.root) as fd,self.assertRaises(BenchmarkError):capture(fd,self.row,maximum=100)
    def test_symlink_parent_rejected(self):
        (self.root/'link').symlink_to(self.root,target_is_directory=True);self.row['path']='link/media'
        with open_root(self.root) as fd,self.assertRaises(BenchmarkError):capture(fd,self.row,maximum=100)
    def test_symlink_root_rejected(self):
        (self.root/'link').symlink_to(self.root,target_is_directory=True)
        with self.assertRaises(BenchmarkError),open_root(self.root/'link'):pass
    def test_directory_not_accepted_as_file(self):
        (self.root/'dir').mkdir();self.row['path']='dir'
        with open_root(self.root) as fd,self.assertRaises(BenchmarkError):capture(fd,self.row,maximum=100)
    def test_fifo_fails_without_waiting(self):
        os.mkfifo(self.root/'fifo');self.row['path']='fifo'
        with open_root(self.root) as fd,self.assertRaises(BenchmarkError):capture(fd,self.row,maximum=100)
    def test_hash_mismatch(self):
        self.row['sha256']='0'*64
        with open_root(self.root) as fd,self.assertRaisesRegex(BenchmarkError,'ADOPTION_HASH_MISMATCH'):capture(fd,self.row,maximum=100)
    def test_size_mismatch(self):
        self.row['size_bytes']=2
        with open_root(self.root) as fd,self.assertRaisesRegex(BenchmarkError,'ADOPTION_SIZE_MISMATCH'):capture(fd,self.row,maximum=100)
    def test_byte_quota_rejects_before_read(self):
        with open_root(self.root) as fd,self.assertRaisesRegex(BenchmarkError,'ADOPTION_BYTE_LIMIT'):capture(fd,self.row,maximum=1)
    def test_frozen_copy_survives_original_change_and_is_removed(self):
        c={'media':self.row,'captions':None}
        with frozen_bundle(self.root,c,LIMITS) as (paths,e):
            p=paths['media'];(self.root/'media').write_bytes(b'changed');self.assertEqual(self.data,p.read_bytes());self.assertEqual(digest(e['files']),e['inventory_sha256'])
        self.assertFalse(p.exists())
    def test_zero_byte_source_manifest_file_can_be_hashed(self):
        (self.root/'empty').write_bytes(b'');row={'path':'empty','sha256':hashlib.sha256(b'').hexdigest(),'size_bytes':0}
        with open_root(self.root) as fd:self.assertEqual(row,capture(fd,row,maximum=10,allow_empty=True))
    def test_duplicate_json_keys_rejected(self):
        (self.root/'j').write_text('{"a":1,"a":2}')
        with self.assertRaises(BenchmarkError):read_confined_json(self.root,'j')
    def test_json_size_limit(self):
        (self.root/'j').write_text('{"a":1}')
        with self.assertRaisesRegex(BenchmarkError,'ADOPTION_JSON_LIMIT'):read_confined_json(self.root,'j',maximum=3)
    def test_json_invalid_utf8(self):
        (self.root/'j').write_bytes(b'\xff')
        with self.assertRaises(BenchmarkError):read_confined_json(self.root,'j')
    def test_missing_file_rejected(self):
        self.row['path']='missing'
        with open_root(self.root) as fd,self.assertRaises(BenchmarkError):capture(fd,self.row,maximum=100)
