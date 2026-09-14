from dataclasses import asdict, replace
import copy, json, tempfile, unittest
from context_fixtures import context_upstream
from teaching_fixtures import teaching_record, TeachingProtocolFixture, context_base
from input_fixtures import upstream
from directing_fixtures import response_record
from bie.director.grounded_directing import model_context, validate_plan, validate_narration, PLAN_SCHEMA, NARRATION_SCHEMA
from bie.director.contextual_teaching import plan_schema, narration_schema, ContextPlannedScene, ContextNarratedScene
from bie.director.director_model import DirectingPolicy, DirectingFailure
from bie.director.director_artifacts import canonical, parse_json
from bie.director.recovery_codec import grounded_record
from bie.director.narration_annotations import verify_base


class ContextTeachingTests(unittest.TestCase):
    def fixture(self, case='science', **kwargs):
        tmp=tempfile.TemporaryDirectory(); self.addCleanup(tmp.cleanup)
        return context_upstream(tmp.name,case,**kwargs)

    def plan(self, f):
        value=parse_json(canonical(teaching_record({'operation':'PLAN','inputs':model_context(f.inputs)})))
        return value,validate_plan(value,f.inputs,DirectingPolicy())

    def narration(self, f, plan, index=0):
        scene=plan.scenes[index]
        value=teaching_record({'operation':'NARRATE','inputs':model_context(f.inputs),'scene':asdict(scene),
            'plan_fingerprint':plan.fingerprint()})
        return parse_json(canonical(value)),scene

    def test_context_free_protocol_and_fingerprint_material_remain_unchanged(self):
        tmp=tempfile.TemporaryDirectory(); self.addCleanup(tmp.cleanup); f=upstream(tmp.name)
        self.assertNotIn('teaching_context',f.inputs.to_model_data())
        self.assertNotIn('teaching_context',model_context(f.inputs))
        self.assertEqual(plan_schema(f.inputs),PLAN_SCHEMA); self.assertEqual(narration_schema(f.inputs),NARRATION_SCHEMA)
        plan=validate_plan(parse_json(canonical(response_record({'operation':'PLAN','inputs':model_context(f.inputs)}))),f.inputs,DirectingPolicy())
        self.assertNotIn('teaching_obligation_ids',asdict(plan.scenes[0]))

    def test_actual_gateway_receives_full_cited_source_and_compiled_context(self):
        f=self.fixture('math'); provider=TeachingProtocolFixture(); b=context_base(f,provider)
        self.assertEqual(len(provider.requests),3)
        for request in provider.requests:
            p=json.loads(request.messages[1]['content'])
            self.assertEqual(p['inputs']['source_pages'][0]['text'],f.text)
            self.assertEqual(p['inputs']['teaching_context']['math'][0]['derivation']['steps'][0]['before'],'x + x')
            self.assertIn('Numerical probes are not proof',request.messages[0]['content'])
        self.assertFalse(b.accepted); self.assertEqual(b.status,'REVIEW_REQUIRED')

    def test_bridge_and_original_assessments_reach_actual_speech(self):
        f=self.fixture(); b=context_base(f)
        self.assertIsInstance(b.plan.scenes[0],ContextPlannedScene)
        self.assertIsInstance(b.narrated_scenes[0],ContextNarratedScene)
        self.assertIn('Electric current is a flow',b.execution.snapshot.utterances[0].text)
        self.assertEqual({i for i,q,a in b.generated_assessment_bindings},{'assessment:charge','assessment:copper'})
        self.assertEqual(set(b.execution.game_handoff.mastery_checks),{'assessment:charge','assessment:copper'})

    def test_plan_cannot_drop_or_repeat_required_bridge_obligation(self):
        f=self.fixture(); value,plan=self.plan(f)
        for ids in ([],list(plan.scenes[0].teaching_obligation_ids)*2):
            bad=copy.deepcopy(value); bad['scenes'][0]['teaching_obligation_ids']=ids
            with self.subTest(ids=ids),self.assertRaises(ValueError): validate_plan(bad,f.inputs,DirectingPolicy())

    def test_obligation_cannot_be_reassigned_to_another_ped_decision(self):
        f=self.fixture(); value,plan=self.plan(f)
        value['scenes'][1]['teaching_obligation_ids']=value['scenes'][0]['teaching_obligation_ids']; value['scenes'][0]['teaching_obligation_ids']=[]
        with self.assertRaisesRegex(ValueError,'another decision'): validate_plan(value,f.inputs,DirectingPolicy())

    def test_prerequisite_order_is_enforced_even_without_a_ped_parent_edge(self):
        f=self.fixture(ped_dependency=False); value,plan=self.plan(f); value['scenes'].reverse()
        for row in value['scenes']: row['parent_scene_ids']=[]
        with self.assertRaisesRegex(ValueError,'prerequisite order'): validate_plan(value,f.inputs,DirectingPolicy())

    def test_declaring_a_bridge_without_explanation_move_is_rejected(self):
        f=self.fixture(); value,plan=self.plan(f); value['scenes'][0]['teaching_moves']=['TRANSITION']
        with self.assertRaisesRegex(ValueError,'teaching move missing'): validate_plan(value,f.inputs,DirectingPolicy())

    def test_original_bridge_assessment_cannot_be_dropped(self):
        f=self.fixture(); value,plan=self.plan(f); value['scenes'][0]['assessment_item_ids']=[]
        with self.assertRaisesRegex(ValueError,'assessment coverage gap'): validate_plan(value,f.inputs,DirectingPolicy())

    def test_math_step_order_is_enforced_across_scenes(self):
        f=self.fixture('math'); value,plan=self.plan(f)
        a,b=value['scenes']; a['teaching_obligation_ids'],b['teaching_obligation_ids']=b['teaching_obligation_ids'],a['teaching_obligation_ids']
        with self.assertRaisesRegex(ValueError,'step order reversed'): validate_plan(value,f.inputs,DirectingPolicy())

    def test_missing_realization_and_fabricated_offsets_are_rejected(self):
        f=self.fixture(); _,plan=self.plan(f); value,scene=self.narration(f,plan)
        for records in ([],[{**value['teaching_realizations'][0],'start_char':1}]):
            bad=copy.deepcopy(value); bad['teaching_realizations']=records
            with self.subTest(records=records),self.assertRaises(ValueError): validate_narration(bad,f.inputs,plan,scene,DirectingPolicy())

    def test_math_symbol_case_and_identifier_suffix_cannot_change_silently(self):
        f=self.fixture('math'); _,plan=self.plan(f); value,scene=self.narration(f,plan)
        for expression in ('X + X','x + xy'):
            bad=copy.deepcopy(value); text=bad['beats'][0]['text'].replace('x + x',expression)
            bad['beats'][0]['text']=text; bad['teaching_realizations'][0].update(quote=text,end_char=len(text))
            with self.subTest(expression=expression),self.assertRaisesRegex(ValueError,'math expression missing'):
                validate_narration(bad,f.inputs,plan,scene,DirectingPolicy())

    def test_beat_index_must_be_an_actual_integer_position(self):
        f=self.fixture('math'); _,plan=self.plan(f); value,scene=self.narration(f,plan)
        for position in (True,-1,100,'0'):
            bad=copy.deepcopy(value); bad['teaching_realizations'][0]['beat_index']=position
            with self.subTest(position=position),self.assertRaisesRegex(ValueError,'beat index'):
                validate_narration(bad,f.inputs,plan,scene,DirectingPolicy())

    def merged_math(self):
        f=self.fixture('math'); value,old=self.plan(f); original=[self.narration(f,old,i)[0] for i in range(2)]
        first=value['scenes'][0]; first['teaching_obligation_ids']+=value['scenes'][1]['teaching_obligation_ids']
        first['assessment_item_ids']=value['scenes'][1]['assessment_item_ids']; value['scenes']=[first]
        plan=validate_plan(value,f.inputs,DirectingPolicy()); narration=original[0]
        narration['plan_fingerprint']=plan.fingerprint(); narration['beats']+=original[1]['beats']
        narration['assessments']=original[1]['assessments']
        narration['teaching_realizations'] += [{**original[1]['teaching_realizations'][0],'beat_index':1}]
        return f,plan,narration

    def test_steps_can_share_a_scene_when_each_has_its_own_ordered_spoken_beat(self):
        f,plan,value=self.merged_math()
        content=validate_narration(value,f.inputs,plan,plan.scenes[0],DirectingPolicy())
        self.assertEqual(len(content.teaching_realizations),2); self.assertEqual(len(content.beats),2)

    def test_reversed_steps_inside_a_scene_are_rejected(self):
        f,plan,value=self.merged_math(); value['beats'].reverse()
        for row in value['teaching_realizations']: row['beat_index']=1-row['beat_index']
        with self.assertRaisesRegex(ValueError,'reversed inside'): validate_narration(value,f.inputs,plan,plan.scenes[0],DirectingPolicy())

    def test_one_paragraph_cannot_masquerade_as_every_math_step(self):
        f,plan,value=self.merged_math(); text=' '.join(b['text'] for b in value['beats'])
        value['beats']=[{**value['beats'][0],'text':text}]
        for row in value['teaching_realizations']: row.update(beat_index=0,start_char=0,end_char=len(text),quote=text)
        with self.assertRaisesRegex(ValueError,'separate actual spoken beats'): validate_narration(value,f.inputs,plan,plan.scenes[0],DirectingPolicy())

    def test_generation_repair_is_bounded_and_cannot_skip_a_required_bridge(self):
        f=self.fixture()
        def drop(p,v,n):
            if p['operation']=='PLAN': v['scenes'][0]['teaching_obligation_ids']=[]
            return v
        provider=TeachingProtocolFixture(drop)
        with self.assertRaises(DirectingFailure): context_base(f,provider)
        self.assertEqual(len(provider.requests),2)

    def test_persisted_rich_result_decodes_and_revalidates_known_types(self):
        f=self.fixture('math'); b=context_base(f)
        decoded=grounded_record(parse_json(canonical(asdict(b))))
        self.assertEqual(decoded,b); verify_base(f.io,f.inputs,decoded)

    def test_decoding_extra_fields_or_removing_obligations_cannot_bypass_validation(self):
        f=self.fixture('math'); b=context_base(f); raw=parse_json(canonical(asdict(b)))
        bad=copy.deepcopy(raw); bad['plan']['scenes'][0]['python_type']='arbitrary.import'
        with self.assertRaises(ValueError): grounded_record(bad)
        bad=copy.deepcopy(raw); del bad['plan']['scenes'][0]['teaching_obligation_ids']
        with self.assertRaises(ValueError): verify_base(f.io,f.inputs,grounded_record(bad))


if __name__=='__main__': unittest.main()
