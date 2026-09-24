"""AUDIO QA source restoration, hostile inputs, real CLI and report truth gates."""
from dataclasses import replace
from pathlib import Path
import hashlib,json,os,subprocess,sys,tempfile,unittest,threading
from unittest.mock import patch
from bie.audio.common import AudioError,fingerprint
from bie.audio.mix_io import publish_mix
from bie.audio.qa_source import load_published_mix,restore_sync
from bie.audio.qa_pipeline import audit_mix
from bie.audio.qa_io import publish_qa
from bie.audio.qa_contract import validate_report,require_qa_pass,check,aggregate,TASKS,Finding
from bie.audio.qa_clipping import FFmpegMeter
from .qa_test_support import native,intent,reseal
ROOT=Path(__file__).resolve().parents[2]

class QAIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sync,cls.mixed,cls.stems=native(True)
        cls.intent=intent(cls.mixed)
        cls.report,cls.captions=audit_mix(cls.mixed,cls.sync,asset_wavs=cls.stems,intent=cls.intent)
    def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
    def tearDown(self):self.tmp.cleanup()
    def publish(self):
        p=self.root/'mix';publish_mix(self.mixed,p,sync=self.sync,inputs={hashlib.sha256(w).hexdigest()+'.wav':w for w in self.stems},allow_review=True);return p
    def mutate(self,p,name,mutator,rehash=False):
        file=p/name;value=json.loads(file.read_text());mutator(value);file.write_text(json.dumps(value))
        if rehash:
            index=json.loads((p/'OUTPUT_SHA256.json').read_text());b=file.read_bytes();index[name]={'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)};(p/'OUTPUT_SHA256.json').write_text(json.dumps(index))
    def test_full_path_reports_all_five_original_tasks(self):self.assertEqual([c['task_id'] for c in self.report['checks']],list(TASKS))
    def test_signal_pass_with_review_not_all_green(self):
        self.assertEqual([c['status'] for c in self.report['checks']],['REVIEW','PASS','PASS','REVIEW','REVIEW']);self.assertEqual(self.report['status'],'REVIEW')
    def test_exact_typed_source_restore_without_provider_calls(self):
        r=restore_sync(json.loads(json.dumps(self.sync.receipt())),self.sync.wav_bytes)
        self.assertEqual(fingerprint(r.receipt()),fingerprint(self.sync.receipt()));self.assertEqual(r.plan,self.sync.plan)
    def test_output_loader_exact(self):
        p=self.publish();m,s,_=load_published_mix(p);self.assertEqual(m.wav_bytes,self.mixed.wav_bytes);self.assertEqual(s.assets,self.sync.assets)
    def test_extra_file_rejected(self):
        p=self.publish();(p/'extra').write_text('bad')
        with self.assertRaises(AudioError):load_published_mix(p)
    def test_missing_source_rejected(self):
        p=self.publish();(p/'source.wav').unlink()
        with self.assertRaises(AudioError):load_published_mix(p)
    def test_symlink_file_rejected(self):
        p=self.publish();(p/'master.wav').unlink();(p/'master.wav').symlink_to(p/'source.wav')
        with self.assertRaises(AudioError):load_published_mix(p)
    def test_symlink_root_rejected(self):
        p=self.publish();link=self.root/'link';link.symlink_to(p,target_is_directory=True)
        with self.assertRaises(AudioError):load_published_mix(link)
    def test_fifo_rejected_without_read_hang(self):
        p=self.publish();os.mkfifo(p/'fifo')
        with self.assertRaises(AudioError):load_published_mix(p)
    def test_wrong_hash_rejected(self):
        p=self.publish();self.mutate(p,'OUTPUT_SHA256.json',lambda x:x['master.wav'].update(sha256='0'*64))
        with self.assertRaises(AudioError):load_published_mix(p)
    def test_negative_size_rejected(self):
        p=self.publish();self.mutate(p,'OUTPUT_SHA256.json',lambda x:x['master.wav'].update(bytes=-1))
        with self.assertRaises(AudioError):load_published_mix(p)
    def test_large_declared_input_budget_rejected(self):
        p=self.publish();self.mutate(p,'OUTPUT_SHA256.json',lambda x:x['master.wav'].update(bytes=10**9))
        with self.assertRaises(AudioError):load_published_mix(p)
    def test_parent_escape_index_rejected(self):
        p=self.publish();self.mutate(p,'OUTPUT_SHA256.json',lambda x:x.update({'../out':{'bytes':3,'sha256':'0'*64}}))
        with self.assertRaises(AudioError):load_published_mix(p)
    def test_duplicate_json_key_rejected(self):
        p=self.publish();(p/'OUTPUT_SHA256.json').write_text('{"x":1,"x":2}')
        with self.assertRaises(AudioError):load_published_mix(p)
    def test_published_captions_rehash_not_enough(self):
        p=self.publish();q=p/'captions.vtt';q.write_text(q.read_text().replace('First','Wrong'))
        index=json.loads((p/'OUTPUT_SHA256.json').read_text());b=q.read_bytes();index['captions.vtt']={'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)};(p/'OUTPUT_SHA256.json').write_text(json.dumps(index))
        with self.assertRaisesRegex(AudioError,'CAPTIONS_CHANGED'):load_published_mix(p)
    def test_source_receipt_missing_task_rejected(self):
        p=self.publish();self.mutate(p,'SOURCE_SYNC.json',lambda x:x['speech_receipts'].pop(),True)
        with self.assertRaises(AudioError):load_published_mix(p)
    def test_source_scope_promoted_rejected(self):
        raw=json.loads(json.dumps(self.sync.receipt()));raw['acoustic_alignment_verified']=True
        with self.assertRaises(AudioError):restore_sync(raw,self.sync.wav_bytes)
    def test_source_selection_changed_rejected(self):
        raw=json.loads(json.dumps(self.sync.receipt()));raw['selection']['catalog_fingerprint']=fingerprint('other')
        with self.assertRaises(AudioError):restore_sync(raw,self.sync.wav_bytes)
    def test_source_timing_end_semantics_changed_rejected(self):
        raw=json.loads(json.dumps(self.sync.receipt()));raw['word_timings'][0]['acoustic_alignment_verified']=True
        with self.assertRaises(AudioError):restore_sync(raw,self.sync.wav_bytes)
    def test_report_exact_roundtrip(self):validate_report(json.loads(json.dumps(self.report)))
    def test_missing_report_check_rejected(self):
        r=json.loads(json.dumps(self.report));r['checks'].pop()
        with self.assertRaises(AudioError):validate_report(r)
    def test_status_bool_tamper_rejected(self):
        r=json.loads(json.dumps(self.report));r['status']='PASS'
        with self.assertRaises(AudioError):validate_report(r)
    def test_rehashed_false_acceptance_rejected(self):
        r=json.loads(json.dumps(self.report));r['product_accepted']=True;r.pop('fingerprint');r['fingerprint']=fingerprint(r)
        with self.assertRaises(AudioError):validate_report(r)
    def test_required_review_findings_cannot_be_erased(self):
        r=json.loads(json.dumps(self.report))
        for c in r['checks']:c['findings']=[];c['status']='PASS'
        r['status']='PASS';r.pop('fingerprint');r['fingerprint']=fingerprint(r)
        with self.assertRaisesRegex(AudioError,'BOUNDARY_MISSING'):validate_report(r)
    def test_review_cannot_authorize_release(self):
        with self.assertRaisesRegex(AudioError,'QA_NOT_PASSED'):require_qa_pass(self.report)
    def test_native_meter_unavailable_is_blocked_not_pass(self):
        m=FFmpegMeter()
        with patch.object(m,'measure',side_effect=AudioError('MIX_FFMPEG_UNAVAILABLE')):
            r,_=audit_mix(self.mixed,self.sync,asset_wavs=self.stems,intent=self.intent,meter=m)
        self.assertEqual(r['checks'][1]['status'],'BLOCKED');self.assertEqual(r['status'],'BLOCKED')
    def test_invalid_clock_cannot_satisfy_remaining_qa(self):
        c=self.mixed.clock();c['words'][0]['spoken']='replacement';r,_=audit_mix(reseal(self.mixed,c),self.sync,asset_wavs=self.stems,intent=self.intent)
        self.assertEqual(r['status'],'FAIL');self.assertEqual(r['checks'][0]['status'],'FAIL')
    def test_cancellation_stops_before_native_work(self):
        flag=threading.Event();flag.set()
        with self.assertRaisesRegex(AudioError,'CANCELLED'):audit_mix(self.mixed,self.sync,cancellation=flag)
    def test_publication_preserves_source(self):
        before=self.mixed.wav_bytes,self.mixed.clock_json;dest=self.root/'qa';index=publish_qa(self.report,self.captions,dest)
        self.assertIn('accessible.vtt',index);self.assertEqual(before,(self.mixed.wav_bytes,self.mixed.clock_json))
    def test_second_publication_rejected(self):
        dest=self.root/'qa';publish_qa(self.report,self.captions,dest)
        with self.assertRaises(AudioError):publish_qa(self.report,self.captions,dest)
    def test_publication_wrong_caption_binding_rejected(self):
        cap=json.loads(json.dumps(self.captions));cap['media_sha256']='0'*64
        with self.assertRaises(AudioError):publish_qa(self.report,cap,self.root/'qa')
    def test_publication_symlink_parent_rejected(self):
        (self.root/'link').symlink_to(self.root,target_is_directory=True)
        with self.assertRaises(AudioError):publish_qa(self.report,self.captions,self.root/'link/qa')
    def test_actual_cli_review_exit_and_reports(self):
        src=self.publish();i=self.root/'intent.json';i.write_text(json.dumps(self.intent));dest=self.root/'qa'
        r=subprocess.run([sys.executable,'-B',str(ROOT/'scripts/audio_qa.py'),str(src),'--output',str(dest),'--caption-intent',str(i),'--standalone-fixture'],capture_output=True,text=True,timeout=30)
        self.assertEqual(r.returncode,3,r.stderr);self.assertEqual(json.loads(r.stdout)['status'],'REVIEW');validate_report(json.loads((dest/'QA_REPORT.json').read_text()))
    def test_cli_cannot_write_inside_source(self):
        src=self.publish();r=subprocess.run([sys.executable,'-B',str(ROOT/'scripts/audio_qa.py'),str(src),'--output',str(src/'qa'),'--standalone-fixture'],capture_output=True,text=True,timeout=30)
        self.assertEqual(r.returncode,2);self.assertFalse((src/'qa').exists())
    def test_cli_missing_input_no_success(self):
        r=subprocess.run([sys.executable,'-B',str(ROOT/'scripts/audio_qa.py'),str(self.root/'missing'),'--output',str(self.root/'qa'),'--standalone-fixture'],capture_output=True,text=True,timeout=30)
        self.assertEqual(r.returncode,2);self.assertFalse((self.root/'qa').exists())
    def test_independent_runs_same_report_identity(self):
        r,c=audit_mix(self.mixed,self.sync,asset_wavs=self.stems,intent=self.intent);self.assertEqual(self.report['fingerprint'],r['fingerprint']);self.assertEqual(self.captions['fingerprint'],c['fingerprint'])
