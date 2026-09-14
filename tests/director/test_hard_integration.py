from dataclasses import replace
import unittest
from examples.director_benchmark import load_suite,controlled_director
from examples.semantic_qa_walkthrough import run
from bie.director.semantic_execution import evaluate_script_semantics
from bie.director.factual_script_qa import factual_qa
from bie.director.qa_contract import snapshot_script,ScriptClaim,bind_span
from bie.director.lesson_architecture_contract import validate_lesson_architecture
from bie.director.script_plan import validate_script_plan
from bie.director.game_handoff import validate_game_handoff
from semantic_fixtures import ProtocolFixtureProvider,IDENTITY,trusted_policy


class HardeningIntegrationTests(unittest.TestCase):
    def test_real_canonical_ped_to_hardened_dir_to_semantic_gateway(self):
        suite,sources=load_suite(); case=suite.cases[-1]; output=controlled_director(case.request)
        validate_lesson_architecture(output.architecture); validate_script_plan(output.snapshot.script); validate_game_handoff(output.game_handoff)
        provider=ProtocolFixtureProvider(); source_ids={p.source_id for p in case.request.catalog.pages}
        result=evaluate_script_semantics(output.snapshot,output.claims,case.request.catalog,tuple(s for s in sources if s.source_id in source_ids),provider,IDENTITY,trusted_policy())
        self.assertEqual(len(provider.requests),2); self.assertEqual(result.status,'CHECKS_PASSED')
        self.assertEqual(output.game_handoff.objective_ids,case.request.pedagogy.objective_ids)
        self.assertFalse(result.accepted)

    def test_narration_edit_invalidates_executed_receipts(self):
        suite,sources=load_suite(); case=suite.cases[0]; output=controlled_director(case.request)
        selected=tuple(s for s in sources if s.source_id==case.request.catalog.pages[0].source_id)
        result=evaluate_script_semantics(output.snapshot,output.claims,case.request.catalog,selected,ProtocolFixtureProvider(),IDENTITY,trusted_policy())
        drafts=(replace(output.snapshot.drafts[0],text='A triangle has four straight sides.'),)
        changed=snapshot_script(output.snapshot.script,drafts,output.snapshot.segment_order)
        claims=(ScriptClaim(output.claims[0].claim_id,bind_span(changed,changed.utterances[0].utterance_id),'FACT',output.claims[0].evidence_ids),)
        with self.assertRaises(ValueError): factual_qa(changed,claims,case.request.catalog,result.receipts,trusted_policy().factual_policy)

    def test_example_fixture_retry_is_not_promoted_to_trusted_semantic_evidence(self):
        result=run(); self.assertEqual(result['provider_calls'],2)
        self.assertEqual(result['status'],'REVIEW_REQUIRED'); self.assertFalse(result['accepted'])
        self.assertFalse(result['live_model_executed']); self.assertEqual(result,run())


if __name__=='__main__': unittest.main()
