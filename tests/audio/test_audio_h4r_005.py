"""H4-R1-005 exported proofs, CLI gates and protected signing-key handling."""
from pathlib import Path
from unittest.mock import patch
from dataclasses import replace
import json
import hashlib
import shutil
import subprocess
import sys
import tempfile
import unittest
from bie.audio.common import AudioError,fingerprint
from bie.audio.acoustic_evidence import load_private_key
from bie.audio.acoustic_contract import canonical
from bie.audio.kernel_io import publish_kernel_evaluation,verify_kernel_publication
from . import kernel_test_support as k
ROOT=Path(__file__).resolve().parents[2]

class DeliveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from bie.audio.qa_pipeline import audit_mix
        cls.c=k.context();cls.r=k.actual_receipt();cls.tmp=tempfile.TemporaryDirectory();cls.addClassCleanup(cls.tmp.cleanup)
        cls.export=Path(cls.tmp.name)/'export'
        result={'kernel_receipt':cls.r,'receipt':cls.r['payload']['compatibility_receipt'],'request':cls.c['request']}
        report,captions=audit_mix(cls.c['mixed'],cls.c['sync'],acoustic_receipt=result['receipt'],evaluator_trust=cls.c['trust']['evaluator_trust'])
        publish_kernel_evaluation(result,cls.c['mixed'],cls.c['sync'],cls.c['runtime'],cls.c['profile'],cls.c['trust'],report,captions,cls.export)
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.path=Path(self.temp.name)/'copy';shutil.copytree(self.export,self.path)
    def check(self,path=None,**override):
        options={'runtime':self.c['runtime'],'profile':self.c['profile'],'trust':self.c['trust']};options.update(override)
        return verify_kernel_publication(path or self.path,self.c['mixed'],self.c['sync'],**options)
    def update_index(self,name):
        p=self.path/'KERNEL_OUTPUT_SHA256.json';m=json.loads(p.read_text());b=(self.path/name).read_bytes()
        m[name]={'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()};p.write_bytes(canonical(m))
    def test_fresh_export_verified(self):self.assertTrue(self.check()['kernel_signature_reverified'])
    def test_extra_file(self):
        (self.path/'unlisted').write_text('extra')
        with self.assertRaises(AudioError):self.check()
    def test_missing_receipt(self):
        (self.path/'KERNEL_RECEIPT.json').unlink()
        with self.assertRaises(AudioError):self.check()
    def test_changed_file(self):
        (self.path/'KERNEL_RECEIPT.json').write_bytes(b'{}')
        with self.assertRaises(AudioError):self.check()
    def test_changed_receipt_and_manifest(self):
        name='KERNEL_RECEIPT.json';r=k.clone(self.r);r['signature_ed25519_hex']='0'*128
        (self.path/name).write_bytes(canonical(r));self.update_index(name)
        with self.assertRaises(AudioError):self.check()
    def test_request_relabel_and_rehash(self):
        name='REQUEST.json';r=k.clone(self.c['request']);r['job_id']='unrelated-run'
        r['fingerprint']=fingerprint({a:b for a,b in r.items() if a!='fingerprint'})
        (self.path/name).write_bytes(canonical(r));self.update_index(name)
        with self.assertRaises(AudioError):self.check()
    def test_symlink_payload(self):
        name=self.path/'KERNEL_PROFILE.json';name.unlink();name.symlink_to(self.export/'KERNEL_PROFILE.json')
        with self.assertRaises(AudioError):self.check()
    def test_revocation_after_export(self):
        t=k.clone(self.c['trust']);t['evaluator_trust']['issuers'][0]['revoked']=True
        with self.assertRaises(AudioError):self.check(trust=t)
    def test_explicit_cli_opt_in(self):
        p=subprocess.run([sys.executable,'-B',str(ROOT/'scripts/audio_kernel.py'),'evaluate','--with-dir-snapshot'],capture_output=True,text=True,timeout=30)
        self.assertEqual(p.returncode,2);self.assertIn('KERNEL_DIAGNOSTIC_OPT_IN_REQUIRED',p.stderr)
    def test_cli_arguments_not_guessed(self):
        p=subprocess.run([sys.executable,'-B',str(ROOT/'scripts/audio_kernel.py'),'evaluate','--with-dir-snapshot','--allow-local-diagnostic'],capture_output=True,text=True,timeout=30)
        self.assertEqual(p.returncode,2);self.assertIn('KERNEL_ARGUMENTS_REQUIRED',p.stderr)
    def test_all_18_dependencies_checked(self):
        from scripts.audio_kernel import verify_dependencies
        verify_dependencies()
        binding=json.loads((ROOT/'docs/evidence/audio-integration-001/CANONICAL_DEPENDENCY_BINDING.json').read_text())
        self.assertEqual(len(binding['files']),18)
    def test_public_key_permissions_not_accepted_for_signer(self):
        p=Path(self.temp.name)/'private';p.write_bytes(b'1'*32);p.chmod(0o644)
        with self.assertRaises(AudioError):load_private_key(p)
    def test_export_never_accepted(self):self.assertFalse(self.check()['product_accepted'])
