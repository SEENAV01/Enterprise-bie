import hashlib,json,os,tempfile,unittest
from pathlib import Path
from cryptography.hazmat.primitives.serialization import Encoding,PrivateFormat,NoEncryption
from bie.audio.common import AudioError
from bie.audio.acoustic_contract import canonical
from bie.audio.pipeline_io import publish_export,verify_export,read_private_key
from bie.audio.qa_source import load_published_mix
from .pipeline_test_support import context,actual,clone,request

class Export(unittest.TestCase):
    def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.c=context()
    def tearDown(self):self.tmp.cleanup()
    def export(self):
        files,receipt=actual();dest=self.root/'published'
        publish_export({'files':files,'receipt':receipt},self.c['request'],self.c['profile'],self.c['trust'],dest,allow_technical_voice=True,allow_review=True)
        return dest
    def test_01_independent_export_verification(self):
        v=verify_export(self.export(),self.c['request'],self.c['profile'],self.c['trust']);self.assertTrue(v['signature_reverified']);self.assertEqual(v['files_verified'],12)
    def test_02_existing_mix_reader_interoperability(self):
        m,s,files=load_published_mix(self.export());self.assertEqual(m.wav_bytes,actual()[0]['master.wav']);self.assertEqual(s.plan.fingerprint(),self.c['request']['plan_fingerprint'])
    def test_03_explicit_technical_voice_opt_in(self):
        f,r=actual()
        with self.assertRaises(AudioError):publish_export({'files':f,'receipt':r},self.c['request'],self.c['profile'],self.c['trust'],self.root/'out',allow_review=True)
    def test_04_explicit_review_opt_in(self):
        f,r=actual()
        with self.assertRaises(AudioError):publish_export({'files':f,'receipt':r},self.c['request'],self.c['profile'],self.c['trust'],self.root/'out',allow_technical_voice=True)
    def test_05_output_not_overwritten(self):
        dest=self.export();original=(dest/'master.wav').read_bytes();f,r=actual()
        with self.assertRaises(AudioError):publish_export({'files':f,'receipt':r},self.c['request'],self.c['profile'],self.c['trust'],dest,allow_technical_voice=True,allow_review=True)
        self.assertEqual(original,(dest/'master.wav').read_bytes())
    def test_06_hash_only_manifest_repair_is_insufficient(self):
        dest=self.export();p=dest/'captions.vtt';p.write_bytes(p.read_bytes()+b'Forged')
        index=json.loads((dest/'OUTPUT_SHA256.json').read_text());index[p.name]={'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()};(dest/'OUTPUT_SHA256.json').write_bytes(canonical(index))
        with self.assertRaises(AudioError):verify_export(dest,self.c['request'],self.c['profile'],self.c['trust'])
    def test_07_missing_export_file(self):
        dest=self.export();(dest/'captions.srt').unlink()
        with self.assertRaises(AudioError):verify_export(dest,self.c['request'],self.c['profile'],self.c['trust'])
    def test_08_extra_export_file(self):
        dest=self.export();(dest/'extra.txt').write_text('x')
        with self.assertRaises(AudioError):verify_export(dest,self.c['request'],self.c['profile'],self.c['trust'])
    def test_09_symlink_export_file(self):
        dest=self.export();p=dest/'captions.srt';data=p.read_bytes();p.unlink();other=self.root/'copy';other.write_bytes(data);p.symlink_to(other)
        with self.assertRaises(AudioError):verify_export(dest,self.c['request'],self.c['profile'],self.c['trust'])
    def test_10_external_expected_request_required(self):
        dest=self.export()
        with self.assertRaises(AudioError):verify_export(dest,request(job_id='different'),self.c['profile'],self.c['trust'])
    def test_11_current_external_trust_required(self):
        dest=self.export();t=clone(self.c['trust']);t['issuers'][0]['revoked']=True
        with self.assertRaises(AudioError):verify_export(dest,self.c['request'],self.c['profile'],t)
    def keyfile(self):
        p=self.root/'private.key';p.write_bytes(self.c['key'].private_bytes(Encoding.Raw,PrivateFormat.Raw,NoEncryption()));p.chmod(0o600);return p
    def test_12_private_key_exact_bytes(self):self.assertIsNotNone(read_private_key(self.keyfile()))
    def test_13_key_group_readable_rejected(self):
        p=self.keyfile();p.chmod(0o640)
        with self.assertRaises(AudioError):read_private_key(p)
    def test_14_key_symlink_rejected(self):
        p=self.keyfile();q=self.root/'link';q.symlink_to(p)
        with self.assertRaises(AudioError):read_private_key(q)
    def test_15_key_hardlink_rejected(self):
        p=self.keyfile();q=self.root/'hard';os.link(p,q)
        with self.assertRaises(AudioError):read_private_key(q)
    def test_16_key_invalid_size_rejected(self):
        p=self.keyfile();p.write_bytes(b'bad')
        with self.assertRaises(AudioError):read_private_key(p)
    def test_17_no_private_key_exported(self):
        dest=self.export();key=self.c['key'].private_bytes(Encoding.Raw,PrivateFormat.Raw,NoEncryption())
        self.assertFalse(any(key in p.read_bytes() for p in dest.iterdir() if p.is_file()))
    def test_18_receipt_acceptance_remains_false(self):
        dest=self.export();p=json.loads((dest/'EXECUTION_RECEIPT.json').read_text())['payload'];self.assertIs(p['product_accepted'],False);self.assertIs(p['live_neural_provider_verified'],False)
    def test_19_symlink_output_root_rejected(self):
        dest=self.export();link=self.root/'link';link.symlink_to(dest,target_is_directory=True)
        with self.assertRaises(AudioError):verify_export(link,self.c['request'],self.c['profile'],self.c['trust'])
