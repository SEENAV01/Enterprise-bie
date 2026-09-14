from dataclasses import asdict,replace
import copy,json,tempfile,unittest
from window_fixtures import long_upstream
from windowed_directing_fixtures import WindowProtocolFixture,windowed_base
from context_fixtures import context_upstream
from bie.director.context_windows import WindowedDirectingPolicy
from bie.director.windowed_directing import WindowedDirectorResult,verify_window_execution
from bie.director.director_model import DirectingPolicy,DirectingFailure
from bie.director.director_artifacts import canonical,parse_json
from bie.director.recovery_codec import grounded_record
from bie.director.narration_annotations import verify_base


class WindowedExecutionTests(unittest.TestCase):
    def fixture(self,**kwargs):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup);return long_upstream(tmp.name,**kwargs)

    def test_old_request_budget_fails_before_transport_and_windows_keep_every_objective(self):
        f=self.fixture(); old=WindowProtocolFixture()
        with self.assertRaises(DirectingFailure) as err:windowed_base(f,old,DirectingPolicy())
        self.assertEqual(err.exception.code,'DIRECTOR_CONTEXT_BUDGET_EXCEEDED');self.assertEqual(old.requests,[])
        provider=WindowProtocolFixture(); b=windowed_base(f,provider)
        self.assertIsInstance(b,WindowedDirectorResult);self.assertEqual(len(b.window_execution.windows),2)
        self.assertEqual({o for s in b.plan.scenes for o in s.objective_ids},{o.objective_id for o in f.objectives})
        self.assertEqual(len(b.generated_assessment_bindings),8);self.assertFalse(b.accepted)

    def test_every_actual_generation_request_fits_the_unchanged_configured_budget(self):
        f=self.fixture(); g=WindowProtocolFixture();p=WindowedDirectingPolicy();b=windowed_base(f,g,p)
        for request in g.requests:
            size=sum(len(m['content']) for m in request.messages)+len(canonical(request.response_schema))
            self.assertLessEqual(size,p.maximum_request_characters)
        verify_window_execution(f.inputs,b)

    def test_all_prior_speech_is_retained_while_transport_uses_a_complete_recent_scene(self):
        f=self.fixture();g=WindowProtocolFixture();b=windowed_base(f,g)
        payloads=[json.loads(r.messages[1]['content']) for r in g.requests]
        narration=[p for p in payloads if p['operation']=='NARRATE_WINDOW']
        self.assertEqual(len(b.narrated_scenes),8);self.assertEqual(len(narration[-1]['completed_scene_ledger']),7)
        self.assertEqual(len(narration[-1]['prior_narration']),1)
        self.assertEqual(narration[-1]['prior_narration'][0],parse_json(canonical(asdict(b.narrated_scenes[-2]))))
        self.assertEqual(narration[-1]['prior_narration_scope']['omitted_from_request_scene_count'],6)
        self.assertTrue(all(p['plan_fingerprint']==b.plan.fingerprint() for p in narration))

    def test_second_plan_window_receives_completed_scene_contracts_and_all_global_goals(self):
        f=self.fixture();g=WindowProtocolFixture();b=windowed_base(f,g)
        plans=[json.loads(r.messages[1]['content']) for r in g.requests if json.loads(r.messages[1]['content'])['operation']=='PLAN_WINDOW']
        self.assertEqual(len(plans[-1]['global_teaching_outline']),8)
        self.assertEqual(tuple(x['scene_id'] for x in plans[-1]['completed_plan_ledger']),b.window_execution.scene_assignments[0][1])

    def test_prerequisite_support_keeps_original_re_and_source_even_without_rich_context(self):
        from bie.director.context_windows import make_window,window_view
        from bie.director.grounded_directing import model_context
        f=self.fixture(units=2,page_characters=500)
        for inputs in (f.inputs,replace(f.inputs,teaching_context=None)):
            window=make_window(inputs,(f.bindings[1].decision_id,),2)
            data=model_context(window_view(inputs,window))
            self.assertEqual({d['decision_id'] for d in data['reasoning']},{d.decision_id for d in f.reasoning})
            self.assertEqual({p['evidence_id'] for p in data['source_passages']},{p.evidence_id for p in f.inputs.catalog.passages})
            self.assertEqual(data['prerequisite_support']['teaching_bindings'][0]['decision_id'],f.bindings[0].decision_id)
            self.assertEqual([b['decision_id'] for b in data['teaching_bindings']],[f.bindings[1].decision_id])

    def test_stale_global_or_window_binding_is_rejected_with_bounded_retry(self):
        f=self.fixture(units=2,page_characters=500)
        for key in ('global_input_fingerprint','window_fingerprint','input_fingerprint'):
            def stale(p,v,n):v[key]='stale';return v
            g=WindowProtocolFixture(stale)
            with self.subTest(key=key),self.assertRaises(DirectingFailure):windowed_base(f,g)
            self.assertEqual(len(g.requests),2)

    def test_scene_namespace_cannot_escape_its_assigned_window(self):
        f=self.fixture(units=1,page_characters=500)
        def change(p,v,n):
            if p['operation']=='PLAN_WINDOW':v['scenes'][0]['scene_id']='another-window:scene'
            return v
        with self.assertRaises(DirectingFailure):windowed_base(f,WindowProtocolFixture(change))

    def test_omitted_original_assessment_blocks_window_plan(self):
        f=self.fixture(units=1,page_characters=500)
        def drop(p,v,n):
            if p['operation']=='PLAN_WINDOW':v['scenes'][0]['assessment_item_ids']=[]
            return v
        with self.assertRaises(DirectingFailure):windowed_base(f,WindowProtocolFixture(drop))

    def test_global_scene_budget_is_enforced_after_individually_valid_windows(self):
        f=self.fixture();g=WindowProtocolFixture()
        with self.assertRaises(DirectingFailure) as err:windowed_base(f,g,WindowedDirectingPolicy(maximum_scenes=7))
        self.assertEqual(err.exception.code,'DIRECTOR_AGGREGATE_OUTPUT_BUDGET_EXCEEDED')
        self.assertTrue(all(json.loads(r.messages[1]['content'])['operation']=='PLAN_WINDOW' for r in g.requests))

    def test_multiple_scenes_per_decision_are_allowed_without_a_fixed_window_layout(self):
        f=self.fixture(units=2,page_characters=500);b=windowed_base(f,WindowProtocolFixture(extra_scene=True))
        self.assertEqual(len(b.plan.scenes),4);self.assertEqual(len(b.generated_assessment_bindings),2)
        self.assertEqual(len(b.window_execution.windows),1);verify_base(f.io,f.inputs,b)

    def test_oversized_recent_narration_fails_instead_of_silently_cutting_continuity(self):
        f=self.fixture();count=[]
        def enlarge(p,v,n):
            if p['operation']=='NARRATE_WINDOW' and not count:
                count.append(n);v['beats'][0]['text']+=' '+p['inputs']['source_pages'][0]['text']*6
            return v
        g=WindowProtocolFixture(enlarge)
        with self.assertRaises(DirectingFailure) as err:windowed_base(f,g)
        self.assertEqual(err.exception.code,'DIRECTOR_CONTEXT_BUDGET_EXCEEDED')
        self.assertEqual(len([r for r in g.requests if json.loads(r.messages[1]['content'])['operation']=='NARRATE_WINDOW']),1)

    def test_late_generation_failure_retains_trace_but_returns_no_partial_lesson(self):
        f=self.fixture(units=2,page_characters=500)
        def break_last(p,v,n):
            if p['operation']=='NARRATE_WINDOW' and p['completed_scene_ledger']:return {}
            return v
        with self.assertRaises(DirectingFailure) as err:windowed_base(f,WindowProtocolFixture(break_last))
        self.assertEqual(len(err.exception.attempts),4)
        self.assertEqual(err.exception.attempts[1].outcome,'VALIDATED_OUTPUT')

    def test_supplied_math_steps_survive_window_generation_and_persistence(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup);f=context_upstream(tmp.name,'math')
        b=windowed_base(f);decoded=grounded_record(parse_json(canonical(asdict(b))))
        self.assertEqual(decoded,b);verify_base(f.io,f.inputs,decoded)
        self.assertEqual(len(decoded.narrated_scenes),2)
        self.assertEqual({x.obligation_id for n in decoded.narrated_scenes for x in n.teaching_realizations},{'math:derivation:algebra:1','math:derivation:algebra:2'})

    def test_edited_continuity_policy_or_window_schedule_cannot_revalidate(self):
        f=self.fixture(units=2,page_characters=500);b=windowed_base(f)
        for record in (replace(b.window_execution,policy=replace(b.window_execution.policy,prior_scene_count=2)),
            replace(b.window_execution,windows=(replace(b.window_execution.windows[0],evidence_ids=()),))):
            with self.subTest(record=record),self.assertRaises(ValueError):verify_base(f.io,f.inputs,replace(b,window_execution=record))

    def test_missing_extra_or_edited_actual_request_evidence_is_rejected(self):
        f=self.fixture(units=2,page_characters=500);b=windowed_base(f)
        cases=(b.generation_attempts[:-1],b.generation_attempts+b.generation_attempts[-1:],
            (replace(b.generation_attempts[0],request_fingerprint='changed'),)+b.generation_attempts[1:])
        for attempts in cases:
            with self.subTest(attempts=attempts),self.assertRaises(ValueError):verify_base(f.io,f.inputs,replace(b,generation_attempts=attempts))

    def test_removing_window_metadata_cannot_bypass_the_known_type_gate(self):
        f=self.fixture(units=1,page_characters=500);b=windowed_base(f);raw=parse_json(canonical(asdict(b)))
        del raw['window_execution']
        with self.assertRaisesRegex(ValueError,'requires its retained'):verify_base(f.io,f.inputs,grounded_record(raw))

    def test_retry_request_fingerprints_reconstruct_after_a_corrected_provider_record(self):
        f=self.fixture(units=1,page_characters=500)
        g=WindowProtocolFixture(lambda p,v,n:{} if n==1 else v);b=windowed_base(f,g)
        self.assertEqual(b.generation_attempts[0].outcome,'RESPONSE_CONTRACT_REJECTED')
        self.assertEqual(b.generation_attempts[1].attempt,2);verify_base(f.io,f.inputs,b)


if __name__=='__main__':unittest.main()
