import unittest
from dataclasses import replace
from bie.director.sync_contract import *
from bie.director.narration_visual_sync import *
from bie.director.pause_timing import PauseCue,build_pause_timing
from bie.director.speech_timing import estimate_speech
from bie.director.emphasis_timing import build_emphasis_timing
from sync_fixtures import context,binding,visual


class VisualSyncTests(unittest.TestCase):
    def test_word_and_character_anchors_map_to_scene_time(self):
        c=context(); p=sync_visual_intents(c,[VisualIntent(binding(c,start=1,end=3),'diagram')])
        w=p.cues[0].window
        self.assertEqual((w.start_ms,w.end_ms),(500,1500))
        self.assertEqual(c.speech.utterances[0].utterance.text[w.start_char:w.end_char],'explain the')
        self.assertEqual(p.cues[0].binding.evidence_ids,('e',))

    def test_internal_pause_is_included_in_anchor_duration(self):
        c=context(); pauses=build_pause_timing(c.speech,[PauseCue('pause','u0',2,500,'Process source',('e',))])
        c=build_sync_context(c.speech,pauses,c.emphasis)
        p=sync_visual_intents(c,[VisualIntent(binding(c,start=1,end=3),'diagram')])
        self.assertEqual((p.cues[0].window.start_ms,p.cues[0].window.end_ms),(500,2000))

    def test_overflow_and_negative_lead_block_without_clamping(self):
        c=context(); p=sync_visual_intents(c,[VisualIntent(binding(c),'diagram',lead_ms=100,tail_ms=300)])
        self.assertEqual(p.status,'BLOCKED')
        self.assertEqual(p.cues[0].window.start_ms,-100)
        self.assertEqual({i.code for i in p.issues},{'LEAD_BEFORE_SCENE','WINDOW_EXCEEDS_SCENE'})

    def test_invalid_bounds_and_ids_rejected(self):
        c=context(); b=binding(c)
        for a in (replace(b.anchor,start_word=True),replace(b.anchor,end_word=99),replace(b.anchor,scene_id='other')):
            with self.subTest(a=a),self.assertRaises(ValueError):
                sync_visual_intents(c,[VisualIntent(replace(b,anchor=a),'diagram')])
        for field,value in (('evidence_ids',('unknown',)),('objective_ids',(' ',)),('concept_ids',()),('intent_id',' ')):
            with self.subTest(field=field),self.assertRaises(ValueError):
                sync_visual_intents(c,[VisualIntent(replace(b,**{field:value}),'diagram')])

    def test_stale_voice_or_text_anchor_rejected(self):
        c=context(); b=binding(c)
        utterances=[replace(c.speech.utterances[0].utterance,voice_id='voice2')]
        s=estimate_speech(utterances); changed=build_sync_context(s,build_pause_timing(s),build_emphasis_timing(s))
        with self.assertRaises(ValueError): sync_visual_intents(changed,[VisualIntent(b,'diagram')])

    def test_edited_timeline_rejected_even_with_old_parent_hashes(self):
        c=context(); scene=c.timeline.scenes[0]
        broken=replace(c.timeline,scenes=(replace(scene,duration_ms=1),))
        with self.assertRaises(ValueError): visual(replace(c,timeline=broken))

    def test_old_visual_plan_rejected_after_wpm_rebuild(self):
        c=context(); p=visual(c)
        with self.assertRaises(ValueError): validate_visual_sync(context(wpm=150),p)

    def test_duplicate_ids_unknown_kinds_and_non_integer_holds_rejected(self):
        c=context(); v=VisualIntent(binding(c),'diagram')
        for rows in ([v,v],[replace(v,kind='unsupported')],[replace(v,tail_ms=True)],[replace(v,lead_ms=float('nan'))]):
            with self.subTest(rows=rows),self.assertRaises(ValueError): sync_visual_intents(c,rows)

    def test_same_target_visibility_overlap_blocks(self):
        c=context(); p=sync_visual_intents(c,[VisualIntent(binding(c,'a'),'diagram'),VisualIntent(binding(c,'b'),'diagram')])
        self.assertIn('OVERLAPPING_VISIBILITY_REQUESTS',{i.code for i in p.issues})

    def test_input_order_and_generators_do_not_change_fingerprint(self):
        c=context(); rows=[VisualIntent(binding(c,'z',target='z'),'diagram'),VisualIntent(binding(c,'a',target='a'),'text')]
        self.assertEqual(sync_visual_intents(c,(r for r in rows)).fingerprint(),sync_visual_intents(c,reversed(rows)).fingerprint())

    def test_empty_plan_abstains_and_no_acceptance_is_claimed(self):
        c=context(); p=sync_visual_intents(c,[])
        self.assertEqual(p.status,'BLOCKED'); self.assertFalse(p.accepted)
        self.assertTrue(visual(c).requires_review)
        self.assertIn('UNCALIBRATED_WPM_ESTIMATE',visual(c).review_reasons)

    def test_cue_tampering_detected(self):
        c=context(); p=visual(c)
        with self.assertRaises(ValueError): validate_visual_sync(c,replace(p,cues=()))
