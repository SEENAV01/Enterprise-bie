import unittest,tempfile,multiprocessing,time
from pathlib import Path
from threading import Event
from bie.audio.neural_scheduler import ProviderCallScheduler
from bie.audio.common import AudioError,fingerprint
from bie.audio.tts_contract import ProviderFailure

KEY=fingerprint('call')

def hold(root,ready,release):
    s=ProviderCallScheduler(root,max_inflight=1,admission_timeout_seconds=2)
    with s.acquire(KEY):
        ready.set();release.wait(5)

class H8SchedulerTests(unittest.TestCase):
    def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)/'slots'
    def test_invalid_inflight_policy(self):
        with self.assertRaisesRegex(AudioError,'INFLIGHT'):ProviderCallScheduler(self.root,max_inflight=0)
    def test_invalid_timeout_policy(self):
        with self.assertRaisesRegex(AudioError,'TIMEOUT'):ProviderCallScheduler(self.root,admission_timeout_seconds=0)
    def test_acquire_returns_bounded_slot_receipt(self):
        s=ProviderCallScheduler(self.root,max_inflight=2)
        with s.acquire(KEY) as r:self.assertIn(r['slot'],(0,1));self.assertFalse(r['distributed_scheduler_verified'])
    def test_cancel_before_admission(self):
        e=Event();e.set();s=ProviderCallScheduler(self.root)
        with self.assertRaisesRegex(ProviderFailure,'CANCELLED'):
            with s.acquire(KEY,cancellation=e):pass
    def test_bad_call_key_rejected(self):
        s=ProviderCallScheduler(self.root)
        with self.assertRaisesRegex(AudioError,'CALL_KEY'):
            with s.acquire('bad'):pass
    def test_cross_process_capacity_timeout(self):
        ctx=multiprocessing.get_context('spawn');ready=ctx.Event();release=ctx.Event();p=ctx.Process(target=hold,args=(self.root,ready,release));p.start()
        try:
            self.assertTrue(ready.wait(3));s=ProviderCallScheduler(self.root,max_inflight=1,admission_timeout_seconds=.15)
            with self.assertRaisesRegex(ProviderFailure,'CAPACITY_TIMEOUT'):
                with s.acquire(KEY):pass
        finally:release.set();p.join(3);self.assertFalse(p.is_alive())
    def test_slot_released_after_context(self):
        s=ProviderCallScheduler(self.root,max_inflight=1,admission_timeout_seconds=.2)
        with s.acquire(KEY):pass
        with s.acquire(KEY) as r:self.assertEqual(r['slot'],0)
    def test_process_death_releases_slot(self):
        ctx=multiprocessing.get_context('spawn');ready=ctx.Event();release=ctx.Event();p=ctx.Process(target=hold,args=(self.root,ready,release));p.start();self.assertTrue(ready.wait(3));p.terminate();p.join(3)
        s=ProviderCallScheduler(self.root,max_inflight=1,admission_timeout_seconds=.5)
        with s.acquire(KEY) as r:self.assertEqual(r['slot'],0)
    def test_two_slots_allow_two_holders(self):
        s=ProviderCallScheduler(self.root,max_inflight=2)
        with s.acquire(KEY) as a:
            with s.acquire(fingerprint('other')) as b:self.assertNotEqual(a['slot'],b['slot'])
    def test_receipt_contains_no_root_path(self):
        s=ProviderCallScheduler(self.root,max_inflight=1)
        with s.acquire(KEY) as r:self.assertNotIn(str(self.root),repr(r))

if __name__=='__main__':unittest.main()
