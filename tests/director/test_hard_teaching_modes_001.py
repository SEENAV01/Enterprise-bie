import tempfile
import unittest
from pathlib import Path

from bie.director.context_windows import WindowedDirectingPolicy
from bie.director.grounded_directing import execute_grounded_director
from bie.director.contextual_teaching import OBLIGATION_MOVES
from bie.director.director_model import DirectingFailure
from context_fixtures import context_upstream
from completion_fixtures import RichTeachingProvider, rich_context
from directing_fixtures import GENERATOR
from semantic_fixtures import ProtocolFixtureProvider, IDENTITY


class RichTeachingModeTests(unittest.TestCase):
    def fixture(self):
        f=context_upstream(Path(tempfile.mkdtemp()),'science');_,_,inputs=rich_context(f)
        return f,inputs

    def execute(self,transform=None,policy=None):
        f,inputs=self.fixture();provider=RichTeachingProvider(transform)
        result=execute_grounded_director(f.io,inputs,provider,GENERATOR,
            ProtocolFixtureProvider(),IDENTITY,policy or WindowedDirectingPolicy(continuity_reserve_characters=1000))
        return f,inputs,provider,result

    def test_actual_director_realizes_all_grounded_strategies_as_separate_beats(self):
        _,inputs,provider,result=self.execute()
        obligations=inputs.teaching_context.obligations
        realized=[r for scene in result.narrated_scenes for r in scene.teaching_realizations]
        self.assertEqual({o.obligation_id for o in obligations},{r.obligation_id for r in realized})
        rich=[o for o in obligations if o.kind not in ('PREREQUISITE_BRIDGE','DERIVATION_STEP')]
        self.assertEqual(17,len(rich));self.assertEqual(1+len(result.plan.scenes),len(provider.requests))

    def test_every_rich_obligation_kind_maps_to_an_existing_director_move(self):
        _,inputs,_,result=self.execute()
        planned={move for scene in result.plan.scenes for move in scene.teaching_moves}
        self.assertTrue({OBLIGATION_MOVES[o.kind] for o in inputs.teaching_context.obligations}<=planned)

    def test_plan_cannot_drop_a_rich_obligation(self):
        def change(payload,value,_):
            if payload['operation']=='PLAN_WINDOW':value['scenes'][-1]['teaching_obligation_ids'].pop()
            return value
        with self.assertRaises(DirectingFailure) as caught:self.execute(change)
        self.assertEqual('RESPONSE_CONTRACT_REJECTED',caught.exception.code)

    def test_narration_cannot_use_the_wrong_teaching_move(self):
        def change(payload,value,_):
            if payload['operation']=='NARRATE_WINDOW' and len(value['beats'])>1:value['beats'][1]['move']='EXPLAIN'
            return value
        with self.assertRaises(DirectingFailure) as caught:self.execute(change)
        self.assertEqual('RESPONSE_CONTRACT_REJECTED',caught.exception.code)

    def test_source_statement_cannot_be_replaced_by_a_generic_activity(self):
        def change(payload,value,_):
            if payload['operation']=='NARRATE_WINDOW' and len(value['beats'])>1:
                value['beats'][1]['text']='Try a generic classroom activity.'
                value['teaching_realizations'][1].update(start_char=0,end_char=len(value['beats'][1]['text']),quote=value['beats'][1]['text'])
            return value
        with self.assertRaises(DirectingFailure):self.execute(change)

    def test_multiple_rich_steps_cannot_share_one_claimed_beat(self):
        def change(payload,value,_):
            if payload['operation']=='NARRATE_WINDOW' and len(value['teaching_realizations'])>2:
                value['teaching_realizations'][2]['beat_index']=1
            return value
        with self.assertRaises(DirectingFailure):self.execute(change)

    def test_assessment_remains_after_rich_teaching(self):
        _,inputs,_,result=self.execute()
        expected={item for b in inputs.bindings for c in b.assessments for item in c.item_ids}
        actual={a.item_id for scene in result.narrated_scenes for a in scene.assessments}
        self.assertEqual(expected,actual);self.assertFalse(result.accepted)

    def test_same_rich_contract_works_on_default_nonwindowed_path(self):
        f,inputs=self.fixture();provider=RichTeachingProvider()
        result=execute_grounded_director(f.io,inputs,provider,GENERATOR,ProtocolFixtureProvider(),IDENTITY)
        self.assertEqual('REVIEW_REQUIRED',result.status)
        self.assertEqual(3,len(provider.requests))


if __name__=='__main__':unittest.main()
