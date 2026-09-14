import unittest
from dataclasses import replace
from bie.scene_ir.contracts import SceneElement,Scene,SpatialIntent,TimeRange,Accessibility,AnimationTrack
from bie.director.sync_contract import build_sync_context
from bie.director.narration_visual_sync import VisualIntent,sync_visual_intents
from bie.director.narration_animation_sync import AnimationIntent,sync_animation_intents,validate_animation_sync
from bie.director.equation_narration_sync import sync_equation_narration,validate_equation_sync
from bie.director.graph_narration_sync import sync_graph_narration,validate_graph_sync,GraphPoint
from bie.director.simulation_narration_sync import sync_simulation_narration,validate_simulation_sync
from bie.director.speech_timing import ReportedAlignment,align_reported_speech
from bie.director.pause_timing import build_pause_timing,PauseCue
from bie.director.emphasis_timing import build_emphasis_timing
from bie.director.wpm_adaptation import ContentLoad,adapt_wpm
from sync_fixtures import context,binding,visual,equation_case,graph_case,simulation_case


class SyncContractTests(unittest.TestCase):
    def test_visual_and_animation_windows_are_consumable_by_existing_scene_ir(self):
        c=context(); v=visual(c); a=sync_animation_intents(c,v,[AnimationIntent(binding(c,'animate',end=2),'v','reveal')])
        vc,ac=v.cues[0],a.cues[0]
        element=SceneElement(vc.binding.target_id,vc.kind,vc.binding.purpose,
            TimeRange(vc.window.start_ms/1000,vc.window.end_ms/1000),SpatialIntent(),
            content={'fixture':'explicit contract bridge, not final generated artwork'},
            animations=[AnimationTrack(ac.binding.intent_id,ac.kind,TimeRange(ac.window.start_ms/1000,ac.window.end_ms/1000),semantic_purpose=ac.binding.purpose)],
            concept_refs=list(vc.binding.concept_ids),learning_objective_refs=list(vc.binding.objective_ids),
            source_artifact_refs=list(vc.binding.evidence_ids),accessibility=Accessibility(label='Source concept diagram'))
        Scene('s','Contract bridge',c.timeline.scenes[0].duration_ms/1000,'Explain source',[element]).validate()
        self.assertEqual(element.animations[0].time.end,1.0)

    def test_wpm_adaptation_invalidates_old_sync_and_explicit_rebuild_uses_new_times(self):
        c=context(); v=visual(c); rows=[AnimationIntent(binding(c,'a',start=1,end=3),'v','reveal')]
        a=sync_animation_intents(c,v,rows)
        adapted=adapt_wpm(c.speech,c.pauses,c.emphasis,ContentLoad(1,1,1,('e',)))
        new=build_sync_context(adapted.candidate_speech,adapted.candidate_pauses,adapted.candidate_emphasis,adapted.candidate_scene_plan)
        with self.assertRaises(ValueError): validate_animation_sync(new,v,a)
        fresh_visual=sync_visual_intents(new,v.inputs)
        fresh=sync_animation_intents(new,fresh_visual,rows)
        self.assertGreater(fresh.cues[0].window.start_ms,a.cues[0].window.start_ms)

    def test_reported_audio_pause_shortfall_blocks_sync_without_retiming(self):
        c=context(); u=c.speech.utterances[0].utterance; n=len(c.speech.utterances[0].words)
        alignment=ReportedAlignment(u.fingerprint(),'sha256:'+'b'*64,n*100,tuple((i*100,(i+1)*100) for i in range(n)),'fixture/1')
        s=align_reported_speech([u],[alignment]); p=build_pause_timing(s,[PauseCue('p','u0',1,400,'Processing hold',('e',))])
        c=build_sync_context(s,p,build_emphasis_timing(s)); v=visual(c)
        a=sync_animation_intents(c,v,[AnimationIntent(binding(c,'a'),'v','reveal')])
        self.assertIn('AUDIO_REPLAN_REQUIRED',{i.code for i in a.issues})
        self.assertEqual(a.timing_basis,'REPORTED_AUDIO_ALIGNMENT')
        self.assertEqual(a.cues[0].window.end_ms,n*100)

    def test_specialized_plans_are_revalidated_against_exact_outputs(self):
        cases=[(equation_case,sync_equation_narration,validate_equation_sync),
               (graph_case,sync_graph_narration,validate_graph_sync),
               (simulation_case,sync_simulation_narration,validate_simulation_sync)]
        for fixture,builder,validator in cases:
            c,v,definition,rows=fixture()
            definitions=definition if isinstance(definition,tuple) else (definition,)
            plan=builder(c,v,definitions,rows)
            self.assertEqual(validator(c,v,plan),plan)
            with self.assertRaises(ValueError): validator(c,v,replace(plan,cues=()))
            with self.assertRaises(ValueError): validator(c,v,replace(plan,review_reasons=()))

    def test_wrong_visual_kind_cannot_consume_domain_specific_intents(self):
        for fixture,builder in ((equation_case,sync_equation_narration),(graph_case,sync_graph_narration),(simulation_case,sync_simulation_narration)):
            c,v,d,rows=fixture(); wrong=sync_visual_intents(c,[replace(v.inputs[0],kind='text')])
            with self.assertRaises(ValueError): builder(c,wrong,d if isinstance(d,tuple) else (d,),rows)

    def test_graph_too_many_samples_for_audio_window_returns_blocker(self):
        c,v,g,rows=graph_case()
        inputs=tuple(t.utterance for t in c.speech.utterances)
        aligns=[]
        for t in c.speech.utterances:
            n=len(t.words)
            aligns.append(ReportedAlignment(t.utterance.fingerprint(),'sha256:'+'c'*64,n,
                tuple((i,i+1) for i in range(n)),'tiny-fixture/1'))
        s=align_reported_speech(inputs,aligns)
        c=build_sync_context(s,build_pause_timing(s),build_emphasis_timing(s)); v=visual(c,'graph')
        g=replace(g,series=(replace(g.series[0],points=tuple(GraphPoint(f'p{i}',i/10,i/5,('e',)) for i in range(11))),))
        rows=tuple(replace(r,graph_fingerprint=g.fingerprint()) for r in rows)
        p=sync_graph_narration(c,v,[g],rows[:2])
        self.assertIn('GRAPH_TRACE_WINDOW_TOO_SHORT',{i.code for i in p.issues})
        self.assertEqual(dict(next(x for x in p.cues if x.kind=='TRACE_SERIES').parameters)['waypoints'],())

    def test_multi_scene_times_are_local_and_target_ids_are_scene_scoped(self):
        from bie.director.speech_timing import estimate_speech
        c=context(); u=c.speech.utterances[0].utterance
        s=estimate_speech((replace(u,scene_id='z'),replace(u,utterance_id='u1',scene_id='a')),wpm=120)
        c=build_sync_context(s,build_pause_timing(s),build_emphasis_timing(s))
        p=sync_visual_intents(c,[VisualIntent(binding(c,'later','u1'),'diagram'),VisualIntent(binding(c,'earlier','u0'),'diagram')])
        self.assertEqual([x.window.scene_id for x in p.cues],['z','a'])
        self.assertEqual([x.window.start_ms for x in p.cues],[0,0])

    def test_all_five_plans_preserve_upstream_review_and_acceptance_boundaries(self):
        from bie.director.speech_timing import estimate_speech
        c=context(); u=replace(c.speech.utterances[0].utterance,review_reasons=('UPSTREAM_REVIEW',))
        s=estimate_speech([u]); c=build_sync_context(s,build_pause_timing(s),build_emphasis_timing(s))
        v=visual(c); a=sync_animation_intents(c,v,[AnimationIntent(binding(c,'a'),'v','reveal')])
        self.assertIn('UPSTREAM_REVIEW',a.review_reasons); self.assertFalse(a.accepted)
        for fixture,builder in ((equation_case,sync_equation_narration),(graph_case,sync_graph_narration),(simulation_case,sync_simulation_narration)):
            c,v,d,rows=fixture(); p=builder(c,v,d if isinstance(d,tuple) else (d,),rows)
            self.assertFalse(p.accepted); self.assertTrue(p.requires_review)
            self.assertIn('INTENT_SCHEDULE_NOT_RENDER_VERIFICATION',p.review_reasons)
