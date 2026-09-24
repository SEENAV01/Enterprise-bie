import json,os,tempfile,unittest
from pathlib import Path
from threading import Event
from unittest.mock import patch
from bie.audio.common import AudioError,fingerprint
from bie.audio.pipeline_runtime import read_output,run_local_pipeline,validate_execution
from bie.audio.pipeline_bundle import validate_bundle,index_files,NAMES
from bie.audio.pipeline_contract import PipelineLimits
from .pipeline_test_support import context,actual,clone,request

class Execution(unittest.TestCase):
    def test_01_actual_native_artifacts(self):
        f,r=actual();self.assertEqual(set(f),NAMES);self.assertTrue(f['master.wav'].startswith(b'RIFF'))
    def test_02_canonical_namespaces_enforced(self):
        _,r=actual();e=r['payload']['execution'];p=e['kernel_proof'];self.assertTrue(p['kernel_enforced'])
        for k,v in e['host_namespaces'].items():self.assertNotEqual(v,p['namespaces'][k])
    def test_03_actual_source_clock_replay(self):
        c=context();f,_=actual();v=validate_bundle(f,c['request'],c['profile']);self.assertEqual(v['sync'].plan.fingerprint(),c['request']['plan_fingerprint'])
    def test_04_precancel_no_native_execution(self):
        c=context();e=Event();e.set()
        with patch('bie.compiler.linux_worker.run_isolated') as run:
            with self.assertRaises(AudioError):run_local_pipeline(c['request'],c['profile'],cancellation=e)
            run.assert_not_called()
    def test_05_unsupported_command_field(self):
        c=context();r=clone(c['request']);r['shell']='true'
        with self.assertRaises(AudioError):run_local_pipeline(r,c['profile'])
    def test_06_caption_modification(self):
        c=context();f,_=actual();f=dict(f);f['captions.vtt']+=b'Wrong captions'
        with self.assertRaises(AudioError):validate_bundle(f,c['request'],c['profile'])
    def test_07_master_modification(self):
        c=context();f,_=actual();f=dict(f);f['master.wav']=f['master.wav'][:-2]+b'\x00\x7f'
        with self.assertRaises(AudioError):validate_bundle(f,c['request'],c['profile'])
    def test_08_missing_file(self):
        f,_=actual();f=dict(f);f.pop('source.wav')
        with self.assertRaises(AudioError):index_files(f,PipelineLimits())
    def test_09_extra_file(self):
        f,_=actual();f={**f,'extra':b'x'}
        with self.assertRaises(AudioError):index_files(f,PipelineLimits())
    def test_10_empty_file(self):
        f,_=actual();f={**f,'captions.srt':b''}
        with self.assertRaises(AudioError):index_files(f,PipelineLimits())
    def test_11_file_byte_budget(self):
        f,_=actual()
        with self.assertRaises(AudioError):index_files(f,PipelineLimits(max_file_bytes=4096))
    def test_12_execution_nonce_rehash(self):
        c=context();f,r=actual();e=clone(r['payload']['execution']);e['nonce']='0'*64;e['fingerprint']=fingerprint({k:v for k,v in e.items() if k!='fingerprint'})
        with self.assertRaises(AudioError):validate_execution(e,f,c['request'],c['profile'])
    def test_13_execution_capability_proof(self):
        c=context();f,r=actual();e=clone(r['payload']['execution']);e['kernel_proof']['capabilities_dropped']=False;e['fingerprint']=fingerprint({k:v for k,v in e.items() if k!='fingerprint'})
        with self.assertRaises(AudioError):validate_execution(e,f,c['request'],c['profile'])
    def test_14_process_exit_type(self):
        c=context();f,r=actual();e=clone(r['payload']['execution']);e['process']['exit_code']=False;e['fingerprint']=fingerprint({k:v for k,v in e.items() if k!='fingerprint'})
        with self.assertRaises(AudioError):validate_execution(e,f,c['request'],c['profile'])
    def test_15_result_file_symlink(self):
        with tempfile.TemporaryDirectory() as td:
            a=Path(td)/'a';a.write_bytes(b'a');b=Path(td)/'b';b.symlink_to(a)
            with self.assertRaises(AudioError):read_output(b,20)
    def test_16_result_file_hardlink(self):
        with tempfile.TemporaryDirectory() as td:
            a=Path(td)/'a';a.write_bytes(b'a');b=Path(td)/'b';os.link(a,b)
            with self.assertRaises(AudioError):read_output(b,20)
    def test_17_result_fifo_nonblocking(self):
        with tempfile.TemporaryDirectory() as td:
            a=Path(td)/'pipe';os.mkfifo(a)
            with self.assertRaises(AudioError):read_output(a,20)
    def test_18_result_directory_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(AudioError):read_output(Path(td),20)
    def test_19_result_regular_file(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'a';p.write_bytes(b'checked');self.assertEqual(read_output(p,7),b'checked')
    def test_20_engine_evidence_changed(self):
        c=context();f,_=actual();f=dict(f);e=json.loads(f['ENGINE_EVIDENCE.json']);e[0]['pcm_sha256']='0'*64;f['ENGINE_EVIDENCE.json']=json.dumps(e).encode()
        with self.assertRaises(AudioError):validate_bundle(f,c['request'],c['profile'])
    def test_21_native_deadline_fails_closed(self):
        c=context();r=request(limits=PipelineLimits(deadline_seconds=1))
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(AudioError):run_local_pipeline(r,c['profile'],lock_root=Path(td)/'slots')
    def test_22_native_duration_budget_not_truncation(self):
        c=context();r=request(limits=PipelineLimits(max_audio_seconds=1))
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(AudioError):run_local_pipeline(r,c['profile'],lock_root=Path(td)/'slots')
