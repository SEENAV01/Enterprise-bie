import copy
import hashlib
import json
import tempfile
import time
import unittest
from dataclasses import replace
from pathlib import Path

from bie.audio.common import AudioError, fingerprint
from bie.audio.pipeline_contract import prepare_document
from bie.audio.segment_cache import (
    SegmentCachePolicy, SegmentCacheStore, build_segment_identity,
    build_segment_receipt, segment_cache_key, validate_segment_identity,
    validate_segment_receipt,
)
from bie.audio.speech_contract import SpeechPlan, SpeechSegment, SpeechSpan
from tests.audio.pipeline_test_support import context

PROVIDER_RECEIPT = fingerprint({'provider':'synthetic-h7'})


def ident():
    c=context(); plan=prepare_document(c['source'])
    return build_segment_identity(plan.segments[0], profile=c['profile'], preparation_profile=plan.profile)


def media(seed=b'a'):
    return (seed * 4096)[:4096]


def receipt(identity, payload):
    return json.dumps(build_segment_receipt(identity,payload,provider_receipt_fingerprint=PROVIDER_RECEIPT),
                      sort_keys=True,separators=(',',':')).encode()


class IdentityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c=context(); cls.plan=prepare_document(cls.c['source']); cls.segment=cls.plan.segments[0]

    def build(self, **kw):
        return build_segment_identity(self.segment, profile=kw.pop('profile',self.c['profile']),
                                      preparation_profile=kw.pop('preparation_profile',self.plan.profile), **kw)

    def test_01_identity_is_deterministic(self): self.assertEqual(self.build(),self.build())
    def test_02_key_is_canonical(self): self.assertRegex(segment_cache_key(self.build()),r'^AUDIO:SEGMENT-CACHE:[0-9a-f]{64}$')
    def test_03_source_refs_preserved(self): self.assertEqual(self.build()['source_refs'],['synthetic:audio-fixture:1'])
    def test_04_run_job_identity_not_present(self):
        value=self.build(); self.assertNotIn('run_id',value); self.assertNotIn('job_id',value)
    def test_05_profile_change_invalidates(self):
        p=copy.deepcopy(self.c['profile']);p['provider_runtime_fingerprint']=fingerprint('different')
        # profile fingerprint must remain self-consistent, so this malformed profile must fail closed.
        with self.assertRaises(Exception):self.build(profile=p)
    def test_06_preparation_profile_change_rejected(self):
        with self.assertRaises(AudioError):self.build(preparation_profile='other')
    def test_07_policy_revision_changes_identity(self):
        a=self.build();b=self.build(policy=SegmentCachePolicy(revision='audio-h7-segment-cache-v2'))
        self.assertNotEqual(a['fingerprint'],b['fingerprint'])
    def test_08_identity_tamper_rejected(self):
        x=copy.deepcopy(self.build());x['segment_id']='tampered'
        with self.assertRaises(AudioError):validate_segment_identity(x)
    def test_09_missing_source_rejected(self):
        x=copy.deepcopy(self.build());x['source_refs']=[];x['fingerprint']=fingerprint({k:v for k,v in x.items() if k!='fingerprint'})
        with self.assertRaises(AudioError):validate_segment_identity(x)
    def test_10_receipt_binds_media(self):
        i=self.build();m=media();r=build_segment_receipt(i,m,provider_receipt_fingerprint=PROVIDER_RECEIPT)
        self.assertEqual(r['media_sha256'],hashlib.sha256(m).hexdigest());validate_segment_receipt(r,i,m)
    def test_11_receipt_wrong_media_rejected(self):
        i=self.build();m=media();r=build_segment_receipt(i,m,provider_receipt_fingerprint=PROVIDER_RECEIPT)
        with self.assertRaises(AudioError):validate_segment_receipt(r,i,media(b'b'))
    def test_12_receipt_acceptance_tamper_rejected(self):
        i=self.build();m=media();r=build_segment_receipt(i,m,provider_receipt_fingerprint=PROVIDER_RECEIPT);r['product_accepted']=True;r['fingerprint']=fingerprint({k:v for k,v in r.items() if k!='fingerprint'})
        with self.assertRaises(AudioError):validate_segment_receipt(r,i,m)


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)/'cache';self.store=SegmentCacheStore(self.root);self.i=ident();self.m=media();self.r=receipt(self.i,self.m)
    def tearDown(self):self.tmp.cleanup()
    def complete(self,*,now=None):
        t=self.store.acquire(self.i,now=now);return self.store.put(t,self.i,self.m,self.r,now=now)
    def test_13_miss_is_false(self):self.assertFalse(self.store.has(self.i))
    def test_14_put_get_roundtrip(self):
        out=self.complete();self.assertEqual(out['speech_bytes'],self.m);self.assertEqual(out['receipt_bytes'],self.r);self.assertTrue(self.store.has(self.i))
    def test_15_restart_persists(self):
        self.complete();other=SegmentCacheStore(self.root);self.assertEqual(other.get(self.i)['speech_bytes'],self.m)
    def test_16_same_completion_is_idempotent(self):
        first=self.complete();ticket=self.store.acquire(self.i);self.assertIsNotNone(ticket.claimed_result_ref);second=self.store.get(self.i);self.assertEqual(first['entry'],second['entry'])
    def test_17_tampered_receipt_rejected_before_publish(self):
        bad=json.loads(self.r);bad['media_sha256']='0'*64;bad['fingerprint']=fingerprint({k:v for k,v in bad.items() if k!='fingerprint'})
        with self.assertRaises(AudioError):self.store.put(self.store.acquire(self.i),self.i,self.m,json.dumps(bad).encode())
    def test_18_wrong_ticket_identity_rejected(self):
        t=self.store.acquire(self.i);other=copy.deepcopy(self.i);other['policy_revision']='audio-h7-segment-cache-v2';other['fingerprint']=fingerprint({k:v for k,v in other.items() if k!='fingerprint'})
        with self.assertRaises(AudioError):self.store.put(t,other,self.m,receipt(other,self.m))
    def test_19_tampered_cas_detected(self):
        out=self.complete();digest=out['entry']['speech']['digest'];path=self.store.cas._path(digest);path.write_bytes(b'corrupt')
        with self.assertRaises((AudioError,Exception)):self.store.get(self.i)
    def test_20_incomplete_claim_not_cache_hit(self):
        self.store.acquire(self.i);self.assertFalse(self.store.has(self.i))
    def test_21_stale_claim_recovery_after_expiry(self):
        now=time.time();old=self.store.acquire(self.i,now=now);new=self.store.acquire(self.i,now=now+31);self.assertGreater(new.lease.epoch,old.lease.epoch);self.store.put(new,self.i,self.m,self.r,now=now+31);self.assertTrue(self.store.has(self.i))
    def test_22_attempt_limit_fail_closed(self):
        p=SegmentCachePolicy(max_attempts=1);s=SegmentCacheStore(Path(self.tmp.name)/'attempt',policy=p);now=time.time();s.acquire(self.i,now=now)
        with self.assertRaises(AudioError):s.acquire(self.i,now=now+31)
    def test_23_media_budget(self):
        p=SegmentCachePolicy(max_segment_bytes=1024,max_receipt_bytes=128,max_cache_bytes=1_000_000);s=SegmentCacheStore(Path(self.tmp.name)/'budget',policy=p)
        with self.assertRaises(AudioError):s.put(s.acquire(self.i),self.i,b'x'*1025,self.r)
    def test_24_orphan_report_dry_run(self):
        ref=self.store.cas.put_bytes(b'orphan');out=self.store.prune_orphans(dry_run=True);self.assertEqual(out['deleted'],0);self.assertEqual([x['digest'] for x in out['orphans']],[ref.digest]);self.assertTrue(self.store.cas.exists(ref))
    def test_25_orphan_prune_removes_only_orphan(self):
        self.complete();orphan=self.store.cas.put_bytes(b'orphan');out=self.store.prune_orphans(dry_run=False);self.assertEqual(out['deleted'],1);self.assertFalse(self.store.cas.exists(orphan));self.assertTrue(self.store.has(self.i))
    def test_26_prune_budget_fail_closed(self):
        self.store.cas.put_bytes(b'a');self.store.cas.put_bytes(b'b')
        with self.assertRaises(AudioError):self.store.prune_orphans(dry_run=False,max_delete=1)
    def test_27_summary_never_claims_acceptance(self):self.assertIs(self.complete()['product_accepted'],False)


if __name__=='__main__':unittest.main()
