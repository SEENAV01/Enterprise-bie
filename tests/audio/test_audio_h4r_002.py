"""H4-R1-002 actual isolated execution and adversarial process/proof contracts."""
from dataclasses import replace
from pathlib import Path
from threading import Event
from types import SimpleNamespace
from unittest.mock import patch
import copy
import hashlib
import json
import os
import tempfile
import unittest
from bie.audio.common import AudioError,fingerprint
from bie.audio.acoustic_contract import AcousticPolicy,build_job
from bie.audio.kernel_runtime import run_kernel,validate_kernel_proof,validate_execution,_result_bytes
from . import kernel_test_support as k

class RuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c=k.context();cls.receipt=k.actual_receipt();cls.e=cls.receipt['payload']['execution']
    def test_actual_namespace_execution(self):
        self.assertEqual(self.e['process']['outcome'],'SUCCEEDED')
        self.assertTrue(self.e['kernel_proof']['kernel_enforced'])
        for n,v in self.e['host_namespaces'].items():self.assertNotEqual(v,self.e['kernel_proof']['namespaces'][n])
    def test_actual_native_passes(self):
        rows=self.receipt['payload']['compatibility_receipt']['payload']['measurement']['segments']
        self.assertTrue(any(len(x['native_passes'])==3 for x in rows))
    def test_media_unmodified(self):self.assertEqual(self.e['media_sha256'],hashlib.sha256(self.c['mixed'].wav_bytes).hexdigest())
    def test_pre_cancel_no_worker(self):
        e=Event();e.set()
        with patch('bie.compiler.linux_worker.run_isolated') as worker:
            with self.assertRaises(AudioError):run_kernel(self.c['job'],self.c['mixed'].wav_bytes,self.c['runtime'],self.c['profile'],cancellation=e)
            worker.assert_not_called()
    def test_namespace_setup_failure_no_fallback(self):
        result=SimpleNamespace(outcome='FAILED',process=SimpleNamespace(passed=False,exit_code=1))
        with patch('bie.compiler.linux_worker.run_isolated',return_value=(result,{'kernel_enforced':False})),patch('bie.audio.acoustic_runtime.run_native') as fallback:
            with self.assertRaisesRegex(AudioError,'KERNEL_FAILED'):run_kernel(self.c['job'],self.c['mixed'].wav_bytes,self.c['runtime'],self.c['profile'])
            fallback.assert_not_called()
    def test_false_success_proof_rejected(self):
        result=SimpleNamespace(outcome='SUCCEEDED',process=SimpleNamespace(passed=True,exit_code=0))
        with patch('bie.compiler.linux_worker.run_isolated',return_value=(result,{})):
            with self.assertRaises(AudioError):run_kernel(self.c['job'],self.c['mixed'].wav_bytes,self.c['runtime'],self.c['profile'])
    def test_result_symlink(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);(p/'a').write_bytes(b'x');(p/'b').symlink_to(p/'a')
            with self.assertRaises(OSError):_result_bytes(p/'b',100)
    def test_result_hardlink(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);(p/'a').write_bytes(b'x');os.link(p/'a',p/'b')
            with self.assertRaises(AudioError):_result_bytes(p/'b',100)
    def test_result_oversize(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'x';p.write_bytes(b'xxx')
            with self.assertRaises(AudioError):_result_bytes(p,2)
    def test_actual_wall_timeout(self):
        j=build_job(self.c['mixed'],self.c['sync'],AcousticPolicy(deadline_seconds=1))
        with self.assertRaisesRegex(AudioError,'KERNEL_TIMED_OUT'):
            run_kernel(j,self.c['mixed'].wav_bytes,self.c['runtime'],self.c['profile'])
    def test_actual_unsupported_hindi_not_pass(self):
        from .qa_test_support import native
        s,m,_=native(language='hindi');j=build_job(m,s)
        measurement,proof=run_kernel(j,m.wav_bytes,self.c['runtime'],self.c['profile'])
        self.assertTrue(all(x['status']=='UNSUPPORTED_LANGUAGE' for x in measurement['segments']))
        self.assertFalse(measurement['pronunciation_verified']);self.assertFalse(proof['product_accepted'])
    def test_execution_hash_tamper(self):
        e=k.clone(self.e);e['nonce']='0'*64
        with self.assertRaises(AudioError):validate_execution(e,self.c['job'],self.c['runtime'],self.c['profile'],self.receipt['payload']['compatibility_receipt']['payload']['measurement'])
    def test_live_host_boundaries(self):
        from scripts.benchmark_audio_kernel import boundary_probe
        with tempfile.TemporaryDirectory() as d:
            result=boundary_probe(Path(d),self.c['profile'])
        self.assertTrue(result['passed']);self.assertTrue(all(result['checks'].values()))

def _proof_bad(path,value):
    def test(self):
        e=k.clone(self.e);d=e['kernel_proof']
        for p in path[:-1]:d=d[p]
        d[path[-1]]=value
        with self.assertRaises(AudioError):validate_kernel_proof(e['kernel_proof'],self.c['profile'],e['host_namespaces'])
    return test
for _name,_path,_value in [
 ('kernel_false',('kernel_enforced',),False),('kernel_int',('kernel_enforced',),1),
 ('procfs',('private_procfs',),True),('network',('private_network',),'HOST'),
 ('no_new_privs',('no_new_privileges',),False),('caps',('capabilities_dropped',),False),
 ('write_root',('read_only_workspace_except_declared',),False),('launcher',('launcher_sha256',),'0'*64),
 ('seccomp',('seccomp_denied_syscalls',),[]),('namespace_format',('namespaces','net'),'not-a-namespace'),
 ('acceptance',('accepted',),True),('limits',('resource_limits','cpu_seconds'),1)]:
    setattr(RuntimeTests,'test_proof_reject_'+_name,_proof_bad(_path,_value))
