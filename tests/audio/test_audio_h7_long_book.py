import copy
import unittest
from dataclasses import replace

from bie.audio.common import AudioError, fingerprint
from bie.audio.long_book import LongBookPolicy, build_long_book_plan, compare_long_book_plans, resume_long_book
from bie.audio.segment_cache import SegmentCachePolicy
from bie.audio.speech_contract import SpeechPlan, SpeechSegment, SpeechSpan
from tests.audio.pipeline_test_support import context

SCRIPT=fingerprint('h7-script')
RULE=fingerprint('h7-rule')

def segment(i,text=None,source=None):
    text=text or ('Segment %d explains a bounded concept.'%i)
    source=source or f'book:p{i}'
    span=SpeechSpan(0,len(text),text,text,'en',RULE,(source,))
    return SpeechSegment(f'seg:{i}',f'utt:{i}',fingerprint(f'utt:{i}:{text}'),SCRIPT,f'scene:{i}','voice:unselected','en',0,len(text),text,(span,),(f'obj:{i}',))

def plan(n=5,overrides=None):
    overrides=overrides or {}
    segs=tuple(overrides.get(i,segment(i)) for i in range(n))
    return SpeechPlan('batch001-144',fingerprint('prep'),fingerprint('lang'),segs)

class LongBookTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.profile=context()['profile']
    def build(self,p=None,**kwargs):return build_long_book_plan(p or plan(),profile=self.profile,**kwargs)
    def test_01_deterministic(self):self.assertEqual(self.build(),self.build())
    def test_02_all_segments_present(self):
        p=self.build();self.assertEqual([x.segment_id for x in p.items],[f'seg:{i}' for i in range(5)])
    def test_03_order_preserved(self):
        p=self.build();self.assertEqual([x.order for x in p.items],list(range(5)))
    def test_04_source_refs_preserved(self):self.assertEqual(self.build().items[2].source_refs,('book:p2',))
    def test_05_segment_count_batch_bound(self):
        p=self.build(policy=LongBookPolicy(max_segments_per_batch=2,max_spoken_chars_per_batch=1000));self.assertEqual([len(b.item_fingerprints) for b in p.batches],[2,2,1])
    def test_06_char_batch_bound(self):
        p=self.build(policy=LongBookPolicy(max_segments_per_batch=10,max_spoken_chars_per_batch=70));self.assertTrue(all(b.spoken_chars<=70 for b in p.batches));self.assertGreater(len(p.batches),1)
    def test_07_no_truncation(self):
        p=self.build();self.assertEqual(sum(len(b.item_fingerprints) for b in p.batches),len(p.items))
    def test_08_single_segment_too_large_rejected(self):
        huge=segment(0,'x'*101)
        with self.assertRaises(AudioError):self.build(plan(1,{0:huge}),policy=LongBookPolicy(max_spoken_chars_per_batch=100))
    def test_09_total_segment_budget(self):
        with self.assertRaises(AudioError):self.build(plan(3),policy=LongBookPolicy(max_total_segments=2))
    def test_10_profile_mismatch_rejected(self):
        with self.assertRaises(AudioError):self.build(preparation_profile='batch001-204')
    def test_11_resume_none(self):
        p=self.build();r=resume_long_book(p,set());self.assertEqual(len(r['pending']),5);self.assertFalse(r['complete'])
    def test_12_resume_partial_keeps_order(self):
        p=self.build();done={p.items[1].identity_fingerprint,p.items[3].identity_fingerprint};r=resume_long_book(p,done);self.assertEqual(r['reused'],(p.items[1].identity_fingerprint,p.items[3].identity_fingerprint));self.assertEqual(len(r['pending']),3)
    def test_13_resume_all(self):
        p=self.build();r=resume_long_book(p,{x.identity_fingerprint for x in p.items});self.assertTrue(r['complete']);self.assertEqual(r['pending'],())
    def test_14_unknown_completion_rejected(self):
        with self.assertRaises(AudioError):resume_long_book(self.build(),{'sha256:'+'0'*64})
    def test_15_same_plan_all_reused(self):
        a=self.build();b=self.build();c=compare_long_book_plans(a,b);self.assertEqual(c['reused'],tuple(f'seg:{i}' for i in range(5)));self.assertEqual(c['invalidated'],())
    def test_16_changed_one_segment_selectively_invalidates(self):
        a=self.build();changed=segment(2,'Segment 2 changed but others remain stable.');b=self.build(plan(5,{2:changed}));c=compare_long_book_plans(a,b);self.assertEqual(c['invalidated'],('seg:2',));self.assertEqual(set(c['reused']),{'seg:0','seg:1','seg:3','seg:4'})
    def test_17_source_ref_change_invalidates_one(self):
        a=self.build();b=self.build(plan(5,{2:segment(2,source='book:new')}));self.assertEqual(compare_long_book_plans(a,b)['invalidated'],('seg:2',))
    def test_18_added_segment_reported(self):
        a=self.build(plan(4));b=self.build(plan(5));self.assertEqual(compare_long_book_plans(a,b)['added'],('seg:4',))
    def test_19_removed_segment_reported(self):
        a=self.build(plan(5));b=self.build(plan(4));self.assertEqual(compare_long_book_plans(a,b)['removed'],('seg:4',))
    def test_20_policy_revision_invalidates_all(self):
        a=self.build();b=self.build(cache_policy=SegmentCachePolicy(revision='audio-h7-segment-cache-v2'));self.assertEqual(set(compare_long_book_plans(a,b)['invalidated']),{f'seg:{i}' for i in range(5)})
    def test_21_fingerprint_stable(self):self.assertEqual(self.build().fingerprint,self.build().fingerprint)
    def test_22_never_product_acceptance(self):self.assertIs(compare_long_book_plans(self.build(),self.build())['product_accepted'],False)

if __name__=='__main__':unittest.main()
