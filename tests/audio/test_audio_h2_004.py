import unittest
from bie.audio.common import AudioError,fingerprint
from bie.audio.acoustic_assessment import assess_receipt
from bie.audio.acoustic_repair import plan_repairs,recheck_repair,immutable_source
from .acoustic_test_support import context,silent_context,clone,receipt,rehash,NOW

class AcousticRepairTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s,cls.m,cls.j,cls.r,cls.res,cls.key,cls.trust=context()
        cls.silent,cls.oldj,cls.oldres,cls.oldrec=silent_context()
    def test_measured_result_is_review_not_pronunciation_pass(self):
        a=assess_receipt(receipt(),self.j,self.trust,now=NOW)
        self.assertEqual(a['status'],'REVIEW');self.assertFalse(a['pronunciation_verified'])
    def test_lexical_disagreement_not_mispronunciation_verdict(self):
        a=assess_receipt(receipt(),self.j,self.trust,now=NOW)
        self.assertTrue(all(f['severity']=='REVIEW' for f in a['findings']))
    def test_exact_final_silence_fails(self):
        a=assess_receipt(self.oldrec,self.oldj,self.trust,now=NOW);self.assertEqual(a['status'],'FAIL')
    def test_intact_dry_speech_routes_silence_to_mix(self):
        a=assess_receipt(self.oldrec,self.oldj,self.trust,now=NOW)
        self.assertTrue(all(f['owner']=='AUDIO/MIX' for f in a['findings']))
    def test_repair_preserves_source_and_reading(self):self.assertEqual(immutable_source(self.oldj),immutable_source(self.j))
    def plan(self):return plan_repairs(self.oldj,self.oldrec,self.trust,now=NOW)
    def test_owned_remix_intent(self):self.assertTrue(all(i['action']=='REMIX_UNCHANGED_READING' for i in self.plan()['items']))
    def test_no_automatic_source_edit_or_kernel_claim(self):
        p=self.plan();self.assertFalse(p['source_or_reading_mutated']);self.assertFalse(p['kernel_dispatch_performed']);self.assertFalse(p['durable_invalidation_performed'])
        self.assertTrue(all(i['automatic_execution_authorized'] is False for i in p['items']))
    def test_downstream_invalidation_targets_present(self):self.assertTrue({'captions','scene_animation_clock','rendered_av'}<=set(self.plan()['downstream_rebuild_required']))
    def test_repair_identity_deterministic(self):self.assertEqual(self.plan(),self.plan())
    def test_valid_fresh_recheck_resolves_exact_silence_not_acceptance(self):
        r=recheck_repair(self.plan(),self.oldj,self.oldrec,self.j,receipt(),self.trust,now=NOW)
        self.assertEqual(len(r['resolved_diagnostic_items']),len(self.plan()['items']));self.assertFalse(r['product_repair_accepted'])
    def test_same_media_recheck_rejected(self):
        with self.assertRaisesRegex(AudioError,'NEW_MEDIA'):recheck_repair(self.plan(),self.oldj,self.oldrec,self.oldj,self.oldrec,self.trust,now=NOW)
    def test_old_receipt_on_new_media_rejected(self):
        with self.assertRaisesRegex(AudioError,'STALE_BINDING'):recheck_repair(self.plan(),self.oldj,self.oldrec,self.j,self.oldrec,self.trust,now=NOW)
    def test_rehashed_repair_tampering_rejected(self):
        p=self.plan();p['items'][0]['owner']='wrong';rehash(p)
        with self.assertRaisesRegex(AudioError,'PLAN_TAMPER'):recheck_repair(p,self.oldj,self.oldrec,self.j,receipt(),self.trust,now=NOW)
    def test_changed_source_refs_cannot_satisfy_repair(self):
        j=clone(self.j);j['segments'][0]['source_spans'][0]['source_refs']=['changed-source'];rehash(j)
        with self.assertRaisesRegex(AudioError,'SOURCE_OR_READING'):recheck_repair(self.plan(),self.oldj,self.oldrec,j,receipt(),self.trust,now=NOW)
    def test_expired_new_evidence_rejected(self):
        with self.assertRaisesRegex(AudioError,'EXPIRED'):recheck_repair(self.plan(),self.oldj,self.oldrec,self.j,receipt(),self.trust,now=NOW+600)
    def test_recheck_no_false_durable_invalidation(self):
        r=recheck_repair(self.plan(),self.oldj,self.oldrec,self.j,receipt(),self.trust,now=NOW)
        self.assertFalse(r['durable_invalidation_performed']);self.assertFalse(r['kernel_dispatch_performed'])
    def test_uncalibrated_phone_disagreement_review_only(self):
        a=assess_receipt(receipt(),self.j,self.trust,now=NOW)
        fs=[f for f in a['findings'] if f['code']=='ACOUSTIC_PHONE_DISAGREEMENT']
        self.assertTrue(fs);self.assertTrue(all(f['severity']=='REVIEW' for f in fs))
    def test_timing_disagreement_does_not_rewrite_clock(self):
        b=clone(self.j);assess_receipt(receipt(),self.j,self.trust,now=NOW);self.assertEqual(b,self.j)
    def test_blocked_new_evaluation_never_closes_previous_failure(self):
        result=clone(self.res)
        for s in result['segments']:
            s['status']='ALIGNMENT_INCOMPLETE';s['words']=[];s['phone_comparisons']=[]
        rehash(result)
        new_receipt=receipt(self.j,result)
        r=recheck_repair(self.plan(),self.oldj,self.oldrec,self.j,new_receipt,self.trust,now=NOW)
        self.assertEqual(r['resolved_diagnostic_items'],[])
