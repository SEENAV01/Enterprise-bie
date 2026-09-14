from dataclasses import replace
import unittest
from bie.director.lesson_architecture_contract import LessonSceneIntent, build_lesson_architecture, validate_lesson_architecture
from bie.director.script_plan import ScriptSegment, build_script_plan, validate_script_plan
from bie.director.game_handoff import build_game_handoff, validate_game_handoff
from bie.director.pacing_plan import build_pacing_plan
from bie.director.scene_purpose_planning import plan_scene_purposes
from bie.director.narrative_arc import build_narrative_arc
from bie.director.hook_strategy import choose_hook
from bie.director.transition_strategy import plan_transition
from bie.director.recap_strategy import plan_recap
from bie.director.emphasis_plan import plan_emphasis
from bie.director.curiosity_gaps import create_curiosity_gap
from bie.director.payoff_structure import bind_payoffs
from bie.director.voiceover_generation import generate_voiceover
from bie.director.dialogue_generation import build_dialogue
from bie.director.persona_selection import select_persona
from bie.director.socratic_dialogue import socratic_sequence
from bie.director.demonstration_narration import narrate_demonstration
from bie.director.derivation_narration import narrate_derivation
from bie.director.misconception_dialogue import build_misconception_dialogue
from bie.director.assessment_prompts import make_assessment_prompt


def scene(**changes):
    return replace(LessonSceneIntent('scene','EXPLAIN',('objective',),('evidence',)),**changes)


def architecture(scenes=None,objectives=('objective',),sources=('source',)):
    return build_lesson_architecture('lesson','Title',(scene(),) if scenes is None else scenes,objectives,sources,'policy/1')


def segment(**changes):
    return replace(ScriptSegment('utterance','scene','EXPLAIN','Explain the grounded concept',('evidence',),('objective',)),**changes)


def handoff(**changes):
    args=dict(lesson_id='lesson',objective_ids=('objective',),concept_ids=('concept',),misconception_ids=(),mastery_checks=('mastery',),evidence_ids=('evidence',))
    args.update(changes); return build_game_handoff(**args)


class HardenedContractsTests(unittest.TestCase):
    def test_scene_cycle_is_rejected_at_producer(self):
        with self.assertRaises(ValueError): architecture((scene(scene_id='a',parent_scene_ids=('b',)),scene(scene_id='b',parent_scene_ids=('a',))))

    def test_deep_dag_does_not_depend_on_python_recursion_limit(self):
        scenes=tuple(scene(scene_id=f's{i}',parent_scene_ids=(f's{i-1}',) if i else ()) for i in range(1500))
        self.assertEqual(len(architecture(scenes).scenes),1500)
        with self.assertRaises(ValueError): architecture((replace(scenes[0],parent_scene_ids=('s1499',)),)+scenes[1:])

    def test_unknown_and_self_parents_are_rejected(self):
        for parent in ('missing','scene'):
            with self.subTest(parent=parent),self.assertRaises(ValueError): architecture((scene(parent_scene_ids=(parent,)),))

    def test_scene_identifiers_cannot_be_blank_or_nonstring(self):
        for field in ('scene_id','purpose'):
            for value in (' ',None,42):
                with self.subTest(field=field,value=value),self.assertRaises(ValueError): architecture((scene(**{field:value}),))
        for field in ('objective_ids','evidence_ids','parent_scene_ids'):
            for value in ((' ',),('valid',None),'single-string'):
                with self.subTest(field=field,value=value),self.assertRaises(ValueError): architecture((scene(**{field:value}),))

    def test_lesson_grounding_and_review_type_are_validated(self):
        for kw in ({'objectives':(' ',)},{'sources':(' ',)},{'sources':'source'}):
            with self.subTest(kw=kw),self.assertRaises(ValueError): architecture(**kw)
        with self.assertRaises(ValueError): architecture((scene(requires_review=1),))
        with self.assertRaises(ValueError): validate_lesson_architecture(replace(architecture(),requires_review=0))

    def test_every_scene_objective_belongs_to_and_covers_lesson(self):
        with self.assertRaises(ValueError): architecture((scene(objective_ids=('other',)),))
        with self.assertRaises(ValueError): architecture(objectives=('objective','uncovered'))

    def test_duplicate_scene_and_parent_ids_are_rejected(self):
        with self.assertRaises(ValueError): architecture((scene(),scene()))
        with self.assertRaises(ValueError): architecture((scene(scene_id='a'),scene(parent_scene_ids=('a','a'))))

    def test_lesson_copies_mutable_source_lists(self):
        evidence=['evidence']; objectives=['objective']; parents=[]
        s=scene(evidence_ids=evidence,objective_ids=objectives,parent_scene_ids=parents)
        a=architecture((s,)); before=a.fingerprint(); evidence.append('changed'); objectives.clear(); parents.append('cycle')
        self.assertEqual(a.fingerprint(),before); self.assertEqual(a.scenes[0].evidence_ids,('evidence',))
        self.assertIs(validate_lesson_architecture(a),a)

    def test_valid_lesson_order_is_canonical_and_review_is_preserved(self):
        a=scene(scene_id='a',requires_review=True); b=scene(scene_id='b',parent_scene_ids=('a',))
        self.assertEqual(architecture((a,b)),architecture((b,a))); self.assertTrue(architecture((b,a)).requires_review)
        with self.assertRaises(ValueError): validate_lesson_architecture(replace(architecture((a,b)),requires_review=False))

    def test_script_checks_every_identifier_and_string_field(self):
        for field in ('segment_id','scene_id','purpose','text_intent'):
            for value in (' ',None,1):
                with self.subTest(field=field,value=value),self.assertRaises(ValueError): build_script_plan('lesson',(segment(**{field:value}),),'voice')
        for field in ('evidence_ids','objective_ids'):
            for value in ((),(' ',),('ok',None),'reference'):
                with self.subTest(field=field,value=value),self.assertRaises(ValueError): build_script_plan('lesson',(segment(**{field:value}),),'voice')

    def test_script_duplicate_segment_and_id_are_rejected(self):
        with self.assertRaises(ValueError): build_script_plan('lesson',(segment(),segment()),'voice')
        with self.assertRaises(ValueError): build_script_plan('lesson',(segment(evidence_ids=('evidence','evidence')),),'voice')

    def test_script_copies_mutable_fields_and_keeps_explicit_canonical_order(self):
        evidence=['evidence']; s=segment(evidence_ids=evidence)
        plan=build_script_plan('lesson',(segment(segment_id='z'),s),'voice'); before=plan.fingerprint(); evidence.clear()
        self.assertEqual(plan.fingerprint(),before); self.assertEqual(plan.segments[0].segment_id,'utterance')
        self.assertIs(validate_script_plan(plan),plan)
        with self.assertRaises(ValueError): validate_script_plan(replace(plan,segments=tuple(reversed(plan.segments))))

    def test_game_required_and_optional_ids_reject_whitespace(self):
        for field in ('objective_ids','concept_ids','mastery_checks','evidence_ids','misconception_ids'):
            for value in ((' ',),('known',None),'single-id'):
                with self.subTest(field=field,value=value),self.assertRaises(ValueError): handoff(**{field:value})
        for field in ('objective_ids','concept_ids','mastery_checks','evidence_ids'):
            with self.subTest(field=field),self.assertRaises(ValueError): handoff(**{field:()})

    def test_game_deduplication_compatibility_and_no_forced_misconception(self):
        self.assertEqual(handoff(objective_ids=['objective','objective']),handoff())
        self.assertIs(validate_game_handoff(handoff()).forbidden_ungrounded_mechanics,True)
        self.assertEqual(handoff().misconception_ids,())

    def test_weakened_game_handoff_is_rejected(self):
        with self.assertRaises(ValueError): validate_game_handoff(replace(handoff(),forbidden_ungrounded_mechanics=False))
        with self.assertRaises(ValueError): validate_game_handoff(replace(handoff(),forbidden_ungrounded_mechanics=1))

    def test_pacing_requires_finite_positive_duration(self):
        for duration in (float('nan'),float('inf'),float('-inf'),0,-1,True,'35',1e308,1e-20,10**1000):
            with self.subTest(duration=duration),self.assertRaises(ValueError): build_pacing_plan((('scene',1.,1.),),duration)

    def test_pacing_load_and_importance_are_real_bounded_numbers(self):
        for value in (float('nan'),float('inf'),-.1,1.1,True,None):
            for row in (('scene',value,.5),('scene',.5,value)):
                with self.subTest(row=row),self.assertRaises(ValueError): build_pacing_plan((row,))

    def test_empty_duplicate_or_malformed_scene_schedule_fails(self):
        for rows in ((),(('a',.5,.5),('a',.3,.3)),((' ',.5,.5),),(('a',.5),),'abc'):
            with self.subTest(rows=rows),self.assertRaises(ValueError): build_pacing_plan(rows)

    def test_pacing_keeps_original_formula_and_can_exceed_arbitrary_video_caps(self):
        result=build_pacing_plan((('scene',.5,.5),),base_seconds=200)
        self.assertEqual(result[0].target_seconds,255)
        self.assertEqual(result[0].pace_band,'NORMAL')

    def test_grounded_helpers_never_promote_blank_ids_or_bare_strings_to_evidence(self):
        calls=(
            lambda ev: plan_scene_purposes((('o','EXPLANATION',ev),)),
            lambda ev: choose_hook('CAUSAL','UNDERSTAND',ev),
            lambda ev: create_curiosity_gap('g','Why?','s',ev),
            lambda ev: bind_payoffs((('g',ev),),{'g':('s','Resolution',('e',))}),
            lambda ev: generate_voiceover('s',('Claim.',),{'Claim.':ev}),
            lambda ev: build_dialogue((('teacher','Why?',ev,'QUESTION'),('learner','Because.',ev,'ANSWER'))),
            lambda ev: socratic_sequence('c','Claim',ev),
            lambda ev: narrate_demonstration('Setup','Act','Observe','Interpret',ev),
            lambda ev: narrate_derivation((('x=1','Given',ev),('y=x','Substitute',ev))),
            lambda ev: build_misconception_dialogue('Belief','Counterevidence','Replacement',ev),
            lambda ev: make_assessment_prompt('o','APPLY','Label',ev),
        )
        for i,call in enumerate(calls):
            for value in ((' ',),('e',None),'evidence'):
                with self.subTest(helper=i,evidence=value),self.assertRaises(ValueError): call(value)

    def test_unresolved_scene_mode_does_not_silently_select_explanation(self):
        for mode in ('UNRESOLVED',' ',None):
            with self.subTest(mode=mode),self.assertRaises(ValueError): plan_scene_purposes((('o',mode,('e',)),))
        for mode in ('EXPLANATION','INQUIRY','DERIVATION','SIMULATION'):
            self.assertTrue(plan_scene_purposes((('o',mode,('e',)),)))

    def test_scores_and_flags_cannot_be_coerced_from_booleans_or_nonfinite_numbers(self):
        for value in (True,float('nan'),float('inf'),-.1,1.1,'0.5'):
            for call in (lambda:build_narrative_arc(value,.5,True),lambda:plan_emphasis((('c',.5,value,.5),))):
                with self.subTest(value=value),self.assertRaises(ValueError): call()
        for value in (1,None,'yes'):
            for call in (lambda:build_narrative_arc(.5,.5,value),lambda:choose_hook('CAUSAL','UNDERSTAND',('e',),value),lambda:plan_recap(('Heat',),transfer_required=value)):
                with self.subTest(flag=value),self.assertRaises(ValueError): call()
        with self.assertRaises(ValueError): plan_emphasis((('c',.5,.5,.5),('c',.5,.5,.5)))
        with self.assertRaises(ValueError): plan_emphasis(())

    def test_text_collections_cannot_accidentally_become_character_sequences(self):
        for labels in ('Heat',('Heat',None),(' ',),()):
            with self.subTest(labels=labels),self.assertRaises(ValueError): plan_recap(labels)
        with self.assertRaises(ValueError): plan_recap(('Heat',),misconceptions='Hotter means more energy')
        for claims in ('Claim.',('Claim.',None),(' ',),()):
            with self.subTest(claims=claims),self.assertRaises(ValueError): generate_voiceover('s',claims,{})
        for call in (lambda:build_dialogue('abcd'),lambda:narrate_derivation(('abc','def'))):
            with self.assertRaises(ValueError): call()

    def test_absent_voiceover_evidence_is_withheld_and_keeps_review(self):
        result=generate_voiceover('s',('Grounded.','Missing.'),{'Grounded.':('e',)})
        self.assertEqual(result.text,'Grounded.')
        self.assertEqual(result.unsupported_claims,('Missing.',))
        self.assertTrue(result.requires_review)
        missing=generate_voiceover('s',('Missing.',),{})
        self.assertEqual(missing.text,''); self.assertTrue(missing.requires_review)

    def test_payoff_binding_requires_complete_distinct_grounded_resolutions(self):
        gap=(('g',('e',)),)
        for resolutions in ({},{'g':('s','Resolution',(' ',))},{'g':('s','Resolution')},{'g':('s',None,('e',))}):
            with self.subTest(resolutions=resolutions),self.assertRaises(ValueError): bind_payoffs(gap,resolutions)
        with self.assertRaises(ValueError): bind_payoffs(gap+gap,{'g':('s','Resolution',('e',))})
        self.assertEqual(bind_payoffs((),{}),())

    def test_helper_text_fields_reject_wrong_types_without_attribute_errors(self):
        for value in (' ',None,42):
            calls=(lambda:select_persona(value,'CAUSAL','EXPLANATION'),
                   lambda:plan_transition('a','b',value),
                   lambda:choose_hook(value,'UNDERSTAND',('e',)),
                   lambda:socratic_sequence('c','Claim',('e',),value),
                   lambda:generate_voiceover('s',('Claim.',),{'Claim.':('e',)},style=value),
                   lambda:narrate_demonstration(value,'Act','Observe','Interpret',('e',)),
                   lambda:make_assessment_prompt('o','APPLY',value,('e',)))
            for i,call in enumerate(calls):
                # None is the deliberate optional misconception default.
                if i==3 and value is None: continue
                with self.subTest(helper=i,value=value),self.assertRaises(ValueError): call()


if __name__=='__main__': unittest.main()
