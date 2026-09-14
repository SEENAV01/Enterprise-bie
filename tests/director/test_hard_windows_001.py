from dataclasses import replace
import json, tempfile, unittest
from window_fixtures import long_upstream
from context_fixtures import context_upstream
from input_fixtures import upstream
from directing_fixtures import GENERATOR, DirectorProtocolFixture
from semantic_fixtures import ProtocolFixtureProvider, IDENTITY
from bie.director.context_windows import (WindowedDirectingPolicy, WindowInputView, build_windows,
    window_view, ordered_decisions, planning_contract)
from bie.director.grounded_directing import model_context, execute_grounded_director
from bie.director.director_model import ResourceLimit, request_material
from bie.director.director_artifacts import canonical, fingerprint


class ContextWindowTests(unittest.TestCase):
    def fixture(self,**kwargs):
        tmp=tempfile.TemporaryDirectory(); self.addCleanup(tmp.cleanup); return long_upstream(tmp.name,**kwargs)

    def short_fixture(self,case='math'):
        tmp=tempfile.TemporaryDirectory(); self.addCleanup(tmp.cleanup); return context_upstream(tmp.name,case)

    def test_large_source_is_partitioned_with_exact_decision_evidence_and_page_coverage(self):
        f=self.fixture(); windows=build_windows(f.inputs,WindowedDirectingPolicy(),GENERATOR)
        self.assertGreater(len(canonical(model_context(f.inputs))),96000)
        self.assertGreater(len(windows),1)
        self.assertEqual(tuple(d for w in windows for d in w.decision_ids),ordered_decisions(f.inputs))
        self.assertEqual({e for w in windows for e in w.evidence_ids},{p.evidence_id for p in f.inputs.catalog.passages})
        self.assertEqual({p for w in windows for p in w.page_fingerprints},{p.fingerprint() for p in f.inputs.catalog.pages})

    def test_complete_cited_pages_keep_the_final_source_condition(self):
        f=self.fixture(); pages={p.page_id:p.text for p in f.inputs.catalog.pages}
        for window in build_windows(f.inputs,WindowedDirectingPolicy(),GENERATOR):
            data=model_context(window_view(f.inputs,window))
            for page in data['source_pages']:
                self.assertEqual(page['text'],pages[page['page_id']]); self.assertTrue(page['text'].endswith(f.conditions[0]))
            self.assertEqual(fingerprint(data),window.context_fingerprint)

    def test_external_prerequisite_support_retains_definitions_conditions_and_source(self):
        f=self.fixture(); windows=build_windows(f.inputs,WindowedDirectingPolicy(),GENERATOR)
        external=next(w for w in windows if w.support_decision_ids)
        data=model_context(window_view(f.inputs,external)); graph=data['teaching_context']['knowledge_graph']['nodes']
        for did in external.support_decision_ids:
            binding=next(b for b in f.bindings if b.decision_id==did)
            objective=next(o for o in f.objectives if o.objective_id==binding.objective_ids[0])
            self.assertIn(objective.concept_id,graph); self.assertTrue(graph[objective.concept_id]['definitions'])
            self.assertTrue(graph[objective.concept_id]['conditions']); self.assertIn(objective.evidence_ids[0],external.evidence_ids)
            self.assertNotIn(did,[b['decision_id'] for b in data['teaching_bindings']])

    def test_view_is_not_a_verified_upstream_artifact_and_cannot_execute_as_one(self):
        f=self.fixture(units=2,page_characters=1000); w=build_windows(f.inputs,WindowedDirectingPolicy(),GENERATOR)[0]
        view=window_view(f.inputs,w); self.assertIsInstance(view,WindowInputView)
        with self.assertRaisesRegex(ValueError,'DirectorInputs required'):
            execute_grounded_director(f.io,view,DirectorProtocolFixture(),GENERATOR,ProtocolFixtureProvider(),IDENTITY)
        with self.assertRaisesRegex(ValueError,'full upstream'): build_windows(view,WindowedDirectingPolicy(),GENERATOR)

    def test_views_do_not_mutate_original_ped_bindings_or_source_artifacts(self):
        f=self.fixture(); before=f.inputs.to_model_data(); records=len(f.io.catalog.records)
        for w in build_windows(f.inputs,WindowedDirectingPolicy(),GENERATOR):
            view=window_view(f.inputs,w); model_context(view); _=view.pedagogy
        self.assertEqual(before,f.inputs.to_model_data()); self.assertEqual(records,len(f.io.catalog.records))

    def test_original_dependency_order_wins_over_a_reversed_binding_list(self):
        f=self.fixture(units=6,page_characters=500,dependencies='chain')
        changed=replace(f.inputs,bindings=tuple(reversed(f.inputs.bindings)))
        self.assertEqual(ordered_decisions(changed),tuple(b.decision_id for b in f.bindings))

    def test_missing_selected_prerequisite_scope_is_an_explicit_error(self):
        f=self.fixture(units=2,page_characters=500)
        with self.assertRaisesRegex(ValueError,'complete selected prerequisite'):
            build_windows(replace(f.inputs,bindings=f.inputs.bindings[1:]),WindowedDirectingPolicy(),GENERATOR)

    def test_window_count_budget_does_not_drop_the_remainder_of_a_lesson(self):
        f=self.fixture(); before=f.inputs.fingerprint()
        with self.assertRaisesRegex(ResourceLimit,'window count'): build_windows(f.inputs,WindowedDirectingPolicy(maximum_windows=1),GENERATOR)
        self.assertEqual(before,f.inputs.fingerprint())

    def test_one_oversized_page_is_never_cut_into_unreviewed_fragments(self):
        f=self.fixture(units=1,page_characters=70000)
        with self.assertRaisesRegex(ResourceLimit,'indivisible'): build_windows(f.inputs,WindowedDirectingPolicy(),GENERATOR)
        self.assertGreater(len(f.inputs.catalog.pages[0].text),70000)

    def test_oversized_upstream_reasoning_is_not_replaced_with_a_summary(self):
        f=self.fixture(units=1,page_characters=500); decision=replace(f.inputs.reasoning[0],selected_option='source-bound tool detail '*6000)
        changed=replace(f.inputs,reasoning=(decision,))
        with self.assertRaisesRegex(ResourceLimit,'indivisible'): build_windows(changed,WindowedDirectingPolicy(),GENERATOR)
        self.assertEqual(changed.reasoning[0].selected_option,decision.selected_option)

    def test_supplied_math_chain_and_its_two_teaching_obligations_stay_together(self):
        f=self.short_fixture(); windows=build_windows(f.inputs,WindowedDirectingPolicy(),GENERATOR)
        self.assertEqual(len(windows),1); data=model_context(window_view(f.inputs,windows[0]))['teaching_context']
        self.assertEqual(len(data['math'][0]['derivation']['steps']),2)
        self.assertEqual(len(data['teaching_obligations']),2)
        self.assertEqual(data['math'][0]['derivation'],f.inputs.teaching_context.model_data()['math'][0]['derivation'])

    def test_cross_lesson_bridge_keeps_original_objectives_and_assessments(self):
        f=self.short_fixture('science'); windows=build_windows(f.inputs,WindowedDirectingPolicy(),GENERATOR)
        bindings=[b for w in windows for b in window_view(f.inputs,w).bindings]
        self.assertEqual({b.decision_id for b in bindings},{b.decision_id for b in f.inputs.bindings})
        self.assertEqual({i for b in bindings for c in b.assessments for i in c.item_ids},{'assessment:charge','assessment:copper'})

    def test_context_free_inputs_still_have_an_explicit_window_view(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup); f=upstream(tmp.name)
        windows=build_windows(f.inputs,WindowedDirectingPolicy(),GENERATOR)
        self.assertNotIn('teaching_context',model_context(window_view(f.inputs,windows[0])))

    def test_window_policy_rejects_invalid_budgets_and_unknown_versions(self):
        for changes in ({'maximum_windows':True},{'maximum_windows':0},{'prior_scene_count':0},
            {'prior_scene_count':True},{'continuity_reserve_characters':96000},{'continuity_reserve_characters':-1},{'window_version':'unknown'}):
            with self.subTest(changes=changes),self.assertRaises(ValueError): WindowedDirectingPolicy(**changes).validate()

    def test_schedule_is_deterministic_and_binds_the_full_input_revision(self):
        f=self.fixture(units=2,page_characters=500); p=WindowedDirectingPolicy()
        a=build_windows(f.inputs,p,GENERATOR); self.assertEqual(a,build_windows(f.inputs,p,GENERATOR))
        b=build_windows(replace(f.inputs,title='Revised lesson title'),p,GENERATOR)
        self.assertNotEqual(a[0].view_fingerprint,b[0].view_fingerprint)

    def test_planning_contract_keeps_global_goals_and_marks_the_view_boundary(self):
        f=self.fixture(); p=WindowedDirectingPolicy(); window=build_windows(f.inputs,p,GENERATOR)[-1]
        payload,schema,prompt=planning_contract(f.inputs,window)
        self.assertEqual(len(payload['global_teaching_outline']),len(f.bindings))
        self.assertEqual(payload['global_input_fingerprint'],f.inputs.fingerprint())
        self.assertEqual(payload['inputs']['input_fingerprint'],window.view_fingerprint)
        self.assertNotEqual(window.view_fingerprint,f.inputs.fingerprint())
        self.assertIn('window_fingerprint',schema['required'])
        self.assertIn('not evidence of learner mastery',prompt)

    def test_request_recipe_matches_actual_existing_gateway_material(self):
        from bie.director.director_model import invoke_structured
        from bie.model_gateway.model_interface import ModelResponse
        from bie.director.grounded_directing import _schema
        class Provider:
            def invoke(self,request):
                self.request=request
                return ModelResponse(GENERATOR.provider,GENERATOR.model,{'answer':'bound'}, {},'completed',{})
        provider=Provider(); policy=WindowedDirectingPolicy(); payload={'original':'source data'}; schema=_schema({'answer':{'type':'string'}})
        value,attempts=invoke_structured(provider,GENERATOR,policy,'PLAN_WINDOW','one','instruction',payload,schema,lambda value:value)
        expected=request_material(GENERATOR,policy,'PLAN_WINDOW','one','instruction',payload,schema)
        self.assertEqual(fingerprint(expected),attempts[0].request_fingerprint)
        self.assertEqual(json.loads(provider.request.messages[1]['content']),payload)


if __name__=='__main__': unittest.main()
