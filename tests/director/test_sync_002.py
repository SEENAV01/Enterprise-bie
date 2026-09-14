import unittest
from dataclasses import replace
from bie.director.narration_animation_sync import *
from bie.director.narration_visual_sync import VisualIntent,sync_visual_intents
from sync_fixtures import context,binding,visual


class AnimationSyncTests(unittest.TestCase):
    def test_dependency_order_and_visual_lifetime(self):
        c=context(); v=visual(c)
        rows=[AnimationIntent(binding(c,'first',start=0,end=1),'v','reveal'),
              AnimationIntent(binding(c,'next',start=1,end=3),'v','emphasize',after_intent_ids=('first',))]
        p=sync_animation_intents(c,v,rows)
        self.assertEqual(p.status,'READY_FOR_DOWNSTREAM_REVIEW')
        self.assertEqual([x.window.start_ms for x in p.cues],[0,500])
        self.assertEqual(p.upstream_fingerprint,v.fingerprint())

    def test_cycle_and_missing_dependency_rejected(self):
        c=context(); v=visual(c); a=AnimationIntent(binding(c,'a'),'v','reveal',after_intent_ids=('b',))
        b=AnimationIntent(binding(c,'b'),'v','emphasize',after_intent_ids=('a',))
        for rows in ([a,b],[a]):
            with self.assertRaises(ValueError): sync_animation_intents(c,v,rows)

    def test_unfinished_dependency_is_explicit_blocker(self):
        c=context(); p=sync_animation_intents(c,visual(c),[
            AnimationIntent(binding(c,'a',end=3),'v','reveal'),
            AnimationIntent(binding(c,'b',start=1,end=2),'v','emphasize',after_intent_ids=('a',))])
        self.assertIn('DEPENDENCY_NOT_FINISHED',{i.code for i in p.issues})

    def test_property_conflicts_cannot_hide_behind_different_kinds(self):
        c=context(); p=sync_animation_intents(c,visual(c),[
            AnimationIntent(binding(c,'a'),'v','path_follow'),AnimationIntent(binding(c,'b'),'v','translate')])
        self.assertIn('ANIMATION_PROPERTY_CONFLICT',{i.code for i in p.issues})

    def test_independent_properties_can_overlap(self):
        c=context(); p=sync_animation_intents(c,visual(c),[
            AnimationIntent(binding(c,'a'),'v','rotate'),AnimationIntent(binding(c,'b'),'v','opacity')])
        self.assertFalse(p.issues)

    def test_too_short_and_outside_visibility_block(self):
        c=context(); v=sync_visual_intents(c,[VisualIntent(binding(c,end=1),'diagram')])
        p=sync_animation_intents(c,v,[AnimationIntent(binding(c,'a',end=2),'v','trace',2000)])
        self.assertEqual({i.code for i in p.issues},{'ANIMATION_WINDOW_TOO_SHORT','OUTSIDE_VISUAL_LIFETIME'})

    def test_unknown_target_and_wrong_source_fail(self):
        c=context(); v=visual(c)
        for row in (AnimationIntent(binding(c),'missing','reveal'),
                    AnimationIntent(binding(c,target='other'),'v','reveal')):
            with self.assertRaises(ValueError): sync_animation_intents(c,v,[row])

    def test_policy_fingerprint_and_generator_stability(self):
        c=context(); v=visual(c); rows=[AnimationIntent(binding(c,'a'),'v','reveal')]
        a=sync_animation_intents(c,v,rows); b=sync_animation_intents(c,v,(x for x in rows))
        self.assertEqual(a.fingerprint(),b.fingerprint())
        self.assertNotEqual(a.fingerprint(),sync_animation_intents(c,v,rows,'policy/2').fingerprint())

    def test_blocked_visual_cannot_be_laundered(self):
        c=context(); v=sync_visual_intents(c,[VisualIntent(binding(c),'diagram',tail_ms=100)])
        p=sync_animation_intents(c,v,[AnimationIntent(binding(c,'a'),'v','reveal')])
        self.assertEqual(p.status,'BLOCKED')
        self.assertIn('WINDOW_EXCEEDS_SCENE',{i.code for i in p.issues})
