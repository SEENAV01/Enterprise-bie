from dataclasses import asdict, replace
import copy, tempfile, unittest
from context_fixtures import context_upstream, publish_context, scored_event, rebind
from input_fixtures import replace_artifact
from bie.director.teaching_context import (KnowledgeConcept, GroundedPrerequisite, TeachingContextPolicy,
    load_teaching_context, publish_teaching_context)
from bie.director.director_inputs import publish_reasoning, publish_pedagogy, load_director_inputs
from bie.prerequisite_intelligence.graph import Edge


class GroundedContextTests(unittest.TestCase):
    def fixture(self, case='science', **kwargs):
        tmp=tempfile.TemporaryDirectory(); self.addCleanup(tmp.cleanup)
        return context_upstream(tmp.name, case, **kwargs)

    def test_real_canonical_graph_order_and_conditions_are_source_bound(self):
        f=self.fixture(); c=f.inputs.teaching_context; data=c.model_data()
        self.assertEqual(data['prerequisite_order'], ['concept:charge','concept:copper'])
        self.assertTrue(data['knowledge_graph_checks']['passed'])
        definition=data['knowledge_graph']['nodes']['concept:charge']['definitions'][0]
        self.assertIn(definition['text'], f.text)
        self.assertIn(definition['anchor_id'], f.io.load_graph((f.context_ref,)))
        self.assertTrue(data['knowledge_graph']['nodes']['concept:copper']['conditions'])
        self.assertEqual(f.io.load(f.pedagogy_ref).parent_refs[-1], f.context_ref)
        self.assertEqual(len(f.inputs.parent_refs),3)

    def test_unknown_mastery_keeps_actual_bridge_objective_and_assessment(self):
        f=self.fixture(); c=f.inputs.teaching_context
        self.assertEqual(c.bridge_decision_ids,('pedagogy:charge',))
        self.assertEqual({o.objective_id for o in f.inputs.objectives},{o.objective_id for o in f.objectives})
        self.assertEqual(f.inputs.bindings[0].assessments, f.bindings[0].assessments)
        self.assertEqual(f.inputs.pedagogy, f.plan)
        self.assertEqual(f.bindings[0].lesson_id,'earlier:science')
        self.assertEqual(f.inputs.bindings[0].lesson_id,'lesson:science')
        for state in c.model_data()['mastery_states']:
            self.assertEqual((state['mean_mastery'],state['lower_bound'],state['upper_bound'],state['confidence']),(.5,0,1,0))
            self.assertEqual(state['observation_ids'],[])

    def test_pr_edge_itself_adds_explicit_bridge_without_a_ped_parent_edge(self):
        f=self.fixture(ped_dependency=False)
        self.assertEqual(f.plan.decisions[-1].parent_decision_ids,())
        self.assertEqual(dict(f.inputs.teaching_context.decision_dependencies)['pedagogy:copper'],('pedagogy:charge',))

    def test_high_reported_mastery_does_not_waive_prerequisite(self):
        f=self.fixture(scores=(1.,1.,1.)); c=f.inputs.teaching_context
        state=next(s for s in c.model_data()['mastery_states'] if s['concept_id']=='concept:charge')
        self.assertEqual(state['mean_mastery'],1.)
        self.assertEqual(set(state['evidence_ids']),{r.artifact_id for r in f.observation_refs})
        self.assertTrue(c.bridge_plan.requires_bridge)
        self.assertTrue(any(o.kind=='PREREQUISITE_BRIDGE' for o in c.obligations))
        self.assertIn('REPORTED_MASTERY_REQUIRES_REVIEW',f.inputs.review_reasons)

    def test_conflicting_scores_preserve_original_uncertainty_report(self):
        f=self.fixture('economics',scores=(0.,1.))
        state=next(s for s in f.inputs.teaching_context.model_data()['mastery_states'] if s['concept_id']=='concept:barter')
        self.assertTrue(state['conflict']); self.assertTrue(state['requires_review'])
        self.assertEqual(state['mean_mastery'],.5)

    def test_exact_excerpt_offsets_cannot_be_replaced_by_matching_text_elsewhere(self):
        f=self.fixture(); c=f.concepts[0]; q=c.definitions[0]
        bad=replace(c,definitions=(replace(q,start_char=q.start_char+1),))
        with self.assertRaisesRegex(ValueError,'quote/offset'): publish_context(f,concepts=(bad,f.concepts[1]))

    def test_missing_definition_or_unknown_excerpt_evidence_is_rejected(self):
        f=self.fixture(); c=f.concepts[0]
        for bad in (replace(c,definitions=()),replace(c,definitions=(replace(c.definitions[0],evidence_id='invented'),))):
            with self.subTest(bad=bad),self.assertRaises(ValueError): publish_context(f,concepts=(bad,f.concepts[1]))

    def test_duplicate_concept_ids_and_nonfinite_edges_are_rejected(self):
        f=self.fixture()
        with self.assertRaises(ValueError): publish_context(f,concepts=(f.concepts[0],f.concepts[0]))
        with self.assertRaises(ValueError): publish_context(f,prerequisites=(replace(f.prerequisites[0],edge=replace(f.prerequisites[0].edge,confidence=float('nan'))),))

    def test_dangling_self_duplicate_and_cyclic_prerequisites_are_rejected(self):
        f=self.fixture(); p=f.prerequisites[0]; a=p.edge.prerequisite; b=p.edge.dependent
        for edges in ((p,p),(replace(p,edge=Edge(a,a)),),(replace(p,edge=Edge('missing',b)),),(p,replace(p,edge=Edge(b,a)))):
            with self.subTest(edges=edges),self.assertRaises(ValueError): publish_context(f,prerequisites=edges)

    def test_orphan_prerequisite_has_no_fabricated_ped_bridge(self):
        f=self.fixture(ped_dependency=False); c=replace(f.concepts[0],concept_id='concept:orphan')
        p=replace(f.prerequisites[0],edge=Edge(c.concept_id,f.concepts[-1].concept_id))
        ref=publish_context(f,concepts=(*f.concepts,c),prerequisites=(p,))
        with self.assertRaisesRegex(ValueError,'missing or ambiguous'): rebind(f,ref)

    def test_context_cannot_drop_a_selected_ped_concept(self):
        f=self.fixture(); ref=publish_context(f,concepts=(f.concepts[0],),prerequisites=())
        with self.assertRaisesRegex(ValueError,'PED concept absent'): rebind(f,ref)

    def test_cross_lesson_prerequisite_without_context_stays_explicit_error(self):
        f=self.fixture()
        ref=publish_pedagogy(f.io,f.run_id,f.source_ref,f.reasoning_ref,f.plan,f.objectives,f.bindings)
        with self.assertRaisesRegex(ValueError,'cross-lesson prerequisite'):
            load_director_inputs(f.io,f.reasoning_ref,ref,run_id=f.run_id,**f.config)

    def test_missing_context_parent_is_rejected(self):
        f=self.fixture(); ref=replace_artifact(f,f.pedagogy_ref,parents=(f.source_ref,f.reasoning_ref))
        with self.assertRaisesRegex(ValueError,'parent refs'):
            load_director_inputs(f.io,f.reasoning_ref,ref,run_id=f.run_id,**f.config)

    def test_edited_tool_reports_and_removed_review_cannot_be_loaded(self):
        f=self.fixture(); data=copy.deepcopy(f.io.load(f.context_ref).payload); data['compiled']['mastery_states'][0]['mean_mastery']=1.
        for ref in (replace_artifact(f,f.context_ref,payload=data),replace_artifact(f,f.context_ref,metadata={'requires_review':False,'accepted':True,'release_ready':True})):
            with self.subTest(ref=ref),self.assertRaisesRegex(ValueError,'output edited or review removed'):
                load_teaching_context(f.io,ref,f.source_ref)

    def test_stale_source_pairing_is_rejected(self):
        f=self.fixture(); other=self.fixture('economics')
        with self.assertRaisesRegex(ValueError,'stale context/source'): load_teaching_context(f.io,f.context_ref,other.source_ref)

    def test_cross_run_context_is_rejected(self):
        f=self.fixture()
        with self.assertRaisesRegex(ValueError,'cross-run'):
            publish_teaching_context(f.io,'another-run',f.source_ref,f.concepts,f.prerequisites)

    def test_book_artifact_cannot_pose_as_a_scored_learner_response(self):
        f=self.fixture()
        with self.assertRaisesRegex(ValueError,'scored assessment event'): publish_context(f,observation_refs=(f.source_ref,))

    def test_mixed_learners_unknown_concepts_and_duplicate_observations_are_rejected(self):
        f=self.fixture(); first=scored_event(f)
        for refs in ((first,first),(first,scored_event(f,learner_key='another-learner')),(scored_event(f,concept_id='unknown'),)):
            with self.subTest(refs=refs),self.assertRaises(ValueError): publish_context(f,observation_refs=refs)

    def test_scored_event_requires_response_origin_and_bounded_numeric_values(self):
        f=self.fixture()
        for changes in ({'score':True},{'score':1.1},{'reliability':-.1},{'age_steps':True},{'response_text':''},{'score_origin':''}):
            with self.subTest(changes=changes),self.assertRaises(ValueError):
                publish_context(f,observation_refs=(scored_event(f,**changes),))

    def test_scored_event_requires_its_actual_source_parent(self):
        f=self.fixture(); event=scored_event(f)
        fake=replace_artifact(f,event,parents=(f.reasoning_ref,))
        with self.assertRaisesRegex(ValueError,'ancestry'): publish_context(f,observation_refs=(fake,))

    def test_context_resource_budget_fails_without_truncating_concepts(self):
        f=self.fixture()
        with self.assertRaisesRegex(ValueError,'resource budget'): publish_context(f,policy=TeachingContextPolicy(maximum_concepts=1))
        self.assertEqual(len(f.inputs.teaching_context.profile.concepts),2)

    def test_math_calls_original_chain_probe_and_teaching_tools_without_claiming_proof(self):
        f=self.fixture('math'); row=f.inputs.teaching_context.model_data()['math'][0]
        self.assertTrue(row['chain']['valid']); self.assertEqual(len(row['numerical_probes']),2)
        self.assertTrue(all(p['equivalent'] for p in row['numerical_probes']))
        self.assertTrue(all(p['explain'] for p in row['teaching_steps']))
        self.assertEqual(row['proof_status'],'NOT_PROVEN_REVIEW_REQUIRED')
        self.assertEqual(len(f.inputs.teaching_context.obligations),2)

    def test_actual_re_derivation_must_equal_the_supplied_source_steps(self):
        f=self.fixture('math'); decision=replace(f.reasoning[0],selected_option='different mathematical result')
        ref=publish_reasoning(f.io,f.run_id,f.source_ref,(decision,),())
        with self.assertRaisesRegex(ValueError,'RE derivation differs'): rebind(f,f.context_ref,reasoning_ref=ref)

    def test_derivation_step_cannot_cite_text_absent_from_source(self):
        f=self.fixture('math'); d=f.derivations[0]; step=replace(d.steps[0],justification='unsupported premise')
        with self.assertRaisesRegex(ValueError,'absent from cited source'):
            publish_context(f,derivations=(replace(d,steps=(step,d.steps[1])),))

    def test_numerical_disagreement_or_disconnected_chain_fails_closed(self):
        cases=((('x + x','3*x','reported rule','reported reason'),),
            (('x + x','2*x','rule one','reason one'),('x + x','x*2','rule two','reason two')))
        for steps in cases:
            with self.subTest(steps=steps),self.assertRaises(ValueError): self.fixture('math',math_steps=steps)

    def test_unsupported_or_unbounded_math_is_rejected_before_probe_execution(self):
        for before in ('abs(x)','x.__class__','2**1000000','(x**12)**12','y+y','x/(x-x)'):
            with self.subTest(before=before),self.assertRaises(ValueError):
                self.fixture('math',math_steps=((before,'2*x','reported rule','reported reason'),))

    def test_rich_derivation_mode_requires_actual_source_steps(self):
        f=self.fixture('math'); ref=publish_context(f,derivations=())
        with self.assertRaisesRegex(ValueError,'actual source-bound steps'): rebind(f,ref)

    def test_a_probe_collision_still_has_no_proof_or_acceptance_authority(self):
        # This polynomial is zero at the original tool's four probes but is
        # not identically zero. A reported match must never become a proof.
        f=self.fixture('math',math_steps=(('x*(x+2)*(x+0.5)*(x-1)*(x-3)','0*x','reported rule','reported reason'),))
        row=f.inputs.teaching_context.model_data()['math'][0]
        self.assertTrue(row['numerical_probes'][0]['equivalent'])
        self.assertEqual(row['proof_status'],'NOT_PROVEN_REVIEW_REQUIRED')
        self.assertFalse(f.io.load(f.context_ref).metadata['accepted'])
        self.assertIn('NUMERICAL_PROBES_ARE_NOT_PROOF',f.inputs.review_reasons)


if __name__=='__main__': unittest.main()
