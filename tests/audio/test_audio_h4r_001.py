"""H4-R1-001 content identities, bounded profile, independent authorization."""
import copy
import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from bie.audio.common import AudioError
from bie.audio.kernel_profile import (canonical_identity,probe_profile,validate_profile,
    engine_sources,read_source,PINNED_BLOBS,KERNEL_SCOPE)
from bie.audio.kernel_evidence import validate_kernel_trust
from . import kernel_test_support as k

class ProfileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.c=k.context()
    def test_eight_original_git_blobs(self):
        rows=canonical_identity();self.assertEqual(len(rows),8)
        for name,blob in PINNED_BLOBS.items():self.assertEqual(rows['bie/compiler/'+name+'.py']['git_blob'],blob)
    def test_current_profile_equal(self):self.assertEqual(validate_profile(self.c['profile'],self.c['runtime']),self.c['profile'])
    def test_profile_reproducible(self):self.assertEqual(probe_profile(self.c['runtime']),self.c['profile'])
    def test_no_signer_or_store_mounted(self):
        self.assertFalse(any('durable_' in p or 'kernel_evidence' in p or 'test' in p for p in engine_sources()))
    def test_actual_dependency_change_rejected(self):
        original=read_source
        def changed(path):
            data=original(path)
            return data+b'\n' if Path(path).name=='linux_worker.py' else data
        with patch('bie.audio.kernel_profile.read_source',side_effect=changed):
            with self.assertRaises(AudioError):canonical_identity()
    def test_unsupported_platform(self):
        with patch('bie.audio.kernel_profile.sys.platform','win32'):
            with self.assertRaises(AudioError):probe_profile(self.c['runtime'])
    def test_source_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);(p/'x').write_text('source');(p/'y').symlink_to(p/'x')
            with self.assertRaises(AudioError):read_source(p/'y')
    def test_source_budget_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'x';p.write_bytes(b'x'*2_000_001)
            with self.assertRaises(AudioError):read_source(p)
    def test_discovery_not_acceptance(self):
        p=self.c['profile'];self.assertFalse(p['product_accepted']);self.assertFalse(p['pronunciation_verified'])
        self.assertEqual(p['calibration_status'],'NOT_ESTABLISHED')
    def test_trust_duplicate_profiles_rejected(self):
        t=k.clone(self.c['trust']);t['profile_fingerprints']*=2
        with self.assertRaises(AudioError):validate_kernel_trust(t)
    def test_trust_empty_profiles_rejected(self):
        t=k.clone(self.c['trust']);t['profile_fingerprints']=[]
        with self.assertRaises(AudioError):validate_kernel_trust(t)
    def test_narrow_policy(self):
        p=self.c['profile']['worker_policy'];self.assertIs(p['procfs'],False)
        self.assertEqual(p['address_space_bytes'],768*1024**2)

def _bad_profile(path,value):
    def test(self):
        p=k.clone(self.c['profile']);d=p
        for key in path[:-1]:d=d[key]
        d[path[-1]]=value
        with self.assertRaises((AudioError,TypeError)):validate_profile(p,self.c['runtime'])
    return test
for _name,_path,_value in [
 ('procfs',('worker_policy','procfs'),True),('unbounded_cpu',('worker_policy','cpu_seconds'),3600),
 ('concurrency_bool',('worker_policy','concurrent_jobs'),True),('operation',('operation',),'OTHER'),
 ('acceptance',('product_accepted',),True),('runtime',('runtime_fingerprint',),'sha256:'+'0'*64),
 ('selected_python',('executables','python','sha256'),'0'*64),('fingerprint',('fingerprint',),'sha256:'+'0'*64),
 ('output_budget',('max_result_bytes',),99_000_000),('unknown_field',('extra',),'forbidden')]:
    setattr(ProfileTests,'test_reject_'+_name,_bad_profile(_path,_value))
