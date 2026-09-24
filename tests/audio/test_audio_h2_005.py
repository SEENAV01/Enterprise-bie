import unittest,tempfile,json,subprocess,sys,os,hashlib
from pathlib import Path
from bie.audio.common import AudioError,fingerprint
from bie.audio.acoustic_contract import AcousticPolicy,canonical
from bie.audio.acoustic_assessment import verify_augmented_qa
from bie.audio.acoustic_io import publish_evaluation,verify_publication,read_evaluation
from bie.audio.qa_pipeline import audit_mix
from bie.audio.qa_contract import validate_report,require_qa_pass
from .acoustic_test_support import context,clone,rehash,receipt,NOW
ROOT=Path(__file__).resolve().parents[2]

class AcousticAdoptionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s,cls.m,cls.j,cls.r,cls.res,cls.key,cls.trust=context()
        cls.receipt=receipt()
        cls.report,cls.captions=audit_mix(cls.m,cls.s,acoustic_receipt=cls.receipt,evaluator_trust=cls.trust,acoustic_now=NOW)
    def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
    def publish(self):
        p=self.root/'evidence';publish_evaluation(self.m,self.s,self.j,self.receipt,self.trust,self.report,self.captions,p,now=NOW);return p
    def test_existing_audit_mix_adopts_receipt(self):self.assertEqual(self.report['binding']['acoustic_receipt_fingerprint'],fingerprint(self.receipt))
    def test_existing_report_validator_retains_fail_closed(self):self.assertEqual(validate_report(self.report),self.report)
    def test_evidence_embedded_in_pronunciation_missing_and_sync_checks(self):
        for i in (0,2,3):self.assertIn('independent_acoustic_evidence',self.report['checks'][i]['metrics'])
    def test_old_review_boundaries_retained(self):
        codes={f['code'] for c in self.report['checks'] for f in c['findings']}
        self.assertTrue({'INDEPENDENT_PRONUNCIATION_UNVERIFIED','INDEPENDENT_ACOUSTIC_ALIGNMENT_UNVERIFIED','ACTUAL_RENDERED_AV_SYNC_UNVERIFIED'}<=codes)
    def test_cannot_release_from_authenticated_diagnostic(self):
        with self.assertRaises(AudioError):require_qa_pass(self.report)
    def test_missing_trust_rejected(self):
        with self.assertRaisesRegex(AudioError,'RECEIPT_AND_TRUST'):audit_mix(self.m,self.s,acoustic_receipt=self.receipt)
    def test_missing_receipt_rejected(self):
        with self.assertRaisesRegex(AudioError,'RECEIPT_AND_TRUST'):audit_mix(self.m,self.s,evaluator_trust=self.trust)
    def test_original_api_remains_available(self):
        r,c=audit_mix(self.m,self.s);self.assertNotIn('acoustic_job_fingerprint',r['binding']);self.assertFalse(r['product_accepted'])
    def test_publication_reloads_against_actual_mix(self):self.assertTrue(verify_publication(self.publish(),self.m,self.s,self.trust,now=NOW)['passed'])
    def test_overwrite_rejected(self):
        p=self.publish()
        with self.assertRaises(AudioError):publish_evaluation(self.m,self.s,self.j,self.receipt,self.trust,self.report,self.captions,p,now=NOW)
    def test_extra_file_rejected(self):
        p=self.publish();(p/'extra').write_text('extra')
        with self.assertRaises(AudioError):read_evaluation(p)
    def test_missing_file_rejected(self):
        p=self.publish();(p/'MEASUREMENT.json').unlink()
        with self.assertRaises(AudioError):read_evaluation(p)
    def test_changed_file_rejected(self):
        p=self.publish();(p/'MEASUREMENT.json').write_text('{}')
        with self.assertRaises(AudioError):read_evaluation(p)
    def test_symlink_member_rejected(self):
        p=self.publish();(p/'MEASUREMENT.json').unlink();(p/'MEASUREMENT.json').symlink_to(p/'JOB.json')
        with self.assertRaises(AudioError):read_evaluation(p)
    def test_signature_mutation_rehashed_manifest_still_rejected(self):
        p=self.publish();n='EVALUATOR_RECEIPT.json';r=json.loads((p/n).read_text());r['signature_ed25519_hex']='0'*128
        (p/n).write_bytes(canonical(r));index=json.loads((p/'OUTPUT_SHA256.json').read_text());index[n]={'sha256':hashlib.sha256((p/n).read_bytes()).hexdigest(),'bytes':(p/n).stat().st_size}
        (p/'OUTPUT_SHA256.json').write_bytes(canonical(index))
        with self.assertRaisesRegex(AudioError,'SIGNATURE_INVALID'):verify_publication(p,self.m,self.s,self.trust,now=NOW)
    def test_rehashed_qa_finding_removal_rejected_by_authenticated_verifier(self):
        r=clone(self.report);r['checks'][0]['findings']=[f for f in r['checks'][0]['findings'] if not f['code'].startswith('ACOUSTIC_')];rehash(r)
        with self.assertRaises(AudioError):verify_augmented_qa(r,self.m,self.s,self.receipt,self.trust,AcousticPolicy(),now=NOW)
    def test_report_not_accepted(self):self.assertFalse(self.report['product_accepted']);self.assertFalse(self.report['actual_remotion_render_verified'])
    def test_cli_help_no_network(self):
        r=subprocess.run([sys.executable,'-B',str(ROOT/'scripts/audio_acoustic.py'),'--help'],capture_output=True,text=True,timeout=10)
        self.assertEqual(r.returncode,0);self.assertIn('allow-local-diagnostic',r.stdout)
    def test_cli_missing_setup_fails_closed(self):
        r=subprocess.run([sys.executable,'-B',str(ROOT/'scripts/audio_acoustic.py'),'evaluate','--with-dir-snapshot'],capture_output=True,text=True,timeout=10)
        self.assertEqual(r.returncode,2);self.assertIn('EXTERNAL_TRUST_REQUIRED',r.stderr)
    def test_published_files_no_private_key(self):
        data=read_evaluation(self.publish());self.assertFalse(any('private' in p.lower() or p.endswith('.key') for p in data))
        self.assertNotIn(self.key.private_bytes_raw(),b''.join(data.values()))
    def test_caption_export_corruption_rehashed_manifests_rejected(self):
        p=self.publish();name='qa/accessible.vtt';(p/name).write_text('WEBVTT\n\ncorrupted\n')
        nested=json.loads((p/'qa/OUTPUT_SHA256.json').read_text())
        nested['accessible.vtt']={'sha256':hashlib.sha256((p/name).read_bytes()).hexdigest(),'bytes':(p/name).stat().st_size}
        (p/'qa/OUTPUT_SHA256.json').write_bytes(canonical(nested))
        index=json.loads((p/'OUTPUT_SHA256.json').read_text())
        for n in (name,'qa/OUTPUT_SHA256.json'):
            index[n]={'sha256':hashlib.sha256((p/n).read_bytes()).hexdigest(),'bytes':(p/n).stat().st_size}
        (p/'OUTPUT_SHA256.json').write_bytes(canonical(index))
        with self.assertRaisesRegex(AudioError,'CAPTION_EXPORT_CHANGED'):verify_publication(p,self.m,self.s,self.trust,now=NOW)
