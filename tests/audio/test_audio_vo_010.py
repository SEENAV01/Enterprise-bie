from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from pathlib import Path
from threading import Event
import hashlib,json,tempfile,unittest
from bie.audio.common import AudioError,fingerprint
from bie.audio.tts_contract import ProviderFailure
from bie.audio.tts_cache import TTSCache,key_lock
from tests.audio.tts_test_support import request

class Caching(unittest.TestCase):
    def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.r,self.p=request();self.c=TTSCache(self.root,namespace='tenant-one')
    def tearDown(self):self.tmp.cleanup()
    def fill(self):return self.c.get_or_generate(self.r,self.p)
    def entry(self):return self.c.entries/self.c.key(self.r)
    def test_first_miss(self):self.assertFalse(self.fill().cache_hit)
    def test_second_hit_no_call(self):
        a=self.fill();b=self.fill();self.assertTrue(b.cache_hit);self.assertEqual(self.p.calls,1);self.assertEqual(a.asset.wav_bytes,b.asset.wav_bytes)
    def test_reload_on_new_cache_instance(self):
        a=self.fill();c=TTSCache(self.root,namespace='tenant-one');b=c.get_or_generate(self.r,self.p);self.assertTrue(b.cache_hit);self.assertEqual(a.asset.receipt(),b.asset.receipt())
    def test_source_revision_miss(self):
        self.fill();r=replace(self.r,plan_fingerprint=fingerprint('changed source'));self.assertFalse(self.c.get_or_generate(r,self.p).cache_hit)
    def test_voice_model_key_changes(self):self.assertNotEqual(self.c.key(self.r),self.c.key(replace(self.r,voice=replace(self.r.voice,model_revision='2'))))
    def test_rate_key_changes(self):self.assertNotEqual(self.c.key(self.r),self.c.key(replace(self.r,settings=replace(self.r.settings,rate_wpm=170))))
    def test_tenant_isolation(self):self.assertNotEqual(self.c.key(self.r),TTSCache(self.root,namespace='tenant-two').key(self.r))
    def test_media_tamper(self):
        self.fill();f=self.entry()/'speech.wav';b=bytearray(f.read_bytes());b[-10]^=1;f.write_bytes(b)
        with self.assertRaisesRegex(AudioError,'IDENTITY'):self.fill()
    def test_missing_media_rejected(self):
        self.fill();(self.entry()/'speech.wav').unlink()
        with self.assertRaisesRegex(AudioError,'INCOMPLETE'):self.fill()
    def test_acceptance_flag_tamper(self):
        self.fill();f=self.entry()/'receipt.json';r=json.loads(f.read_text());r['product_accepted']=True;f.write_text(json.dumps(r))
        with self.assertRaisesRegex(AudioError,'ACCEPTANCE'):self.fill()
    def test_request_identity_tamper(self):
        self.fill();f=self.entry()/'receipt.json';r=json.loads(f.read_text());r['request_fingerprint']=fingerprint('wrong');f.write_text(json.dumps(r))
        with self.assertRaisesRegex(AudioError,'IDENTITY'):self.fill()
    def test_symlink_media_rejected(self):
        self.fill();f=self.entry()/'speech.wav';original=f.read_bytes();f.unlink();target=self.root/'outside';target.write_bytes(original);f.symlink_to(target)
        with self.assertRaisesRegex(AudioError,'CACHE_FILE'):self.fill()
    def test_symlink_root_rejected(self):
        target=self.root/'link';target.symlink_to(self.c.root,target_is_directory=True)
        with self.assertRaisesRegex(AudioError,'SYMLINK'):TTSCache(target,namespace='other')
    def test_concurrent_single_generation(self):
        with ThreadPoolExecutor(max_workers=3) as pool:results=list(pool.map(lambda _:self.fill(),range(3)))
        self.assertEqual(self.p.calls,1);self.assertEqual(sum(x.cache_hit for x in results),2)
    def test_failed_provider_not_cached(self):
        self.p.failures=[ProviderFailure('FAILED')]
        with self.assertRaises(ProviderFailure):self.fill()
        self.assertFalse(self.entry().exists());self.assertFalse(any(self.c.entries.iterdir()))
    def test_cancelled_cache_hit_respected(self):
        self.fill();e=Event();e.set()
        with self.assertRaisesRegex(ProviderFailure,'CANCELLED'):self.c.get_or_generate(self.r,self.p,cancellation=e)
    def test_lock_timeout(self):
        p=self.c.locks/(self.c.key(self.r)+'.lock');self.c.lock_timeout=.05
        with key_lock(p,timeout=1):
            with self.assertRaisesRegex(AudioError,'TIMEOUT'):self.fill()
    def test_extra_file_blocked(self):
        self.fill();(self.entry()/'unexpected').write_text('x')
        with self.assertRaisesRegex(AudioError,'INCOMPLETE'):self.fill()
    def test_cache_returns_verified_sample_metadata(self):self.assertEqual(self.fill().asset.info.samples_per_channel,2205)
    def test_runtime_metadata_tamper(self):
        self.fill();f=self.entry()/'receipt.json';r=json.loads(f.read_text());r['request']['voice']['runtime_fingerprint']=fingerprint('stale');f.write_text(json.dumps(r))
        with self.assertRaisesRegex(AudioError,'IDENTITY'):self.fill()
