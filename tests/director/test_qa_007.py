from dataclasses import replace
import unittest
from examples.director_benchmark import load_suite, controlled_director
from bie.director.director_benchmark import (CandidateIdentity, DirectorRequest, NarrativeExpectation, FindingExpectation,
    run_director_benchmark)
from bie.director.qa_contract import snapshot_script, ScriptClaim, bind_span
from bie.director.source_grounding_qa import SourceBytes
from bie.director.speech_timing import estimate_speech
from bie.director.pause_timing import build_pause_timing
from bie.director.emphasis_timing import build_emphasis_timing
from bie.director.scene_duration_fit import fit_scene_durations
from bie.pedagogy.pedagogy_plan_contract import build_pedagogy_plan

IDENTITY=CandidateIdentity("test-adapter","1","sha256:"+"a"*64,"sha256:"+"b"*64)


def respeak(output,texts,order=None):
    by_id=dict(zip(output.snapshot.segment_order,texts))
    drafts=tuple(replace(d,text=by_id[d.segment_id]) for d in output.snapshot.drafts)
    snapshot=snapshot_script(output.snapshot.script,drafts,order or output.snapshot.segment_order)
    claims=tuple(ScriptClaim("c:"+u.utterance_id,bind_span(snapshot,u.utterance_id),"FACT",u.evidence_ids) for u in snapshot.utterances)
    speech=estimate_speech(snapshot.utterances); pauses=build_pause_timing(speech); emphasis=build_emphasis_timing(speech)
    return replace(output,snapshot=snapshot,claims=claims,speech=speech,pauses=pauses,emphasis=emphasis,
        timeline=fit_scene_durations(speech,pauses,emphasis),discourse=(),pacing=())


class DirectorBenchmarkTests(unittest.TestCase):
    def setUp(self): self.suite,self.sources=load_suite()
    def run_suite(self,candidate=controlled_director,**kwargs):
        return run_director_benchmark(kwargs.pop('suite',self.suite),candidate,kwargs.pop('sources',self.sources),IDENTITY,**kwargs)

    def test_actual_execution_three_domains_and_retained_qa_review(self):
        r=self.run_suite(); self.assertTrue(r.checks_passed); self.assertEqual(len(r.attempts),12)
        self.assertEqual(r.domain_results,(("MATH",2,2),("SCIENCE",2,2),("ECONOMICS",2,2)))
        self.assertEqual(r.qa_status,"REVIEW_REQUIRED"); self.assertFalse(r.accepted)
        self.assertTrue(all(len(a.reports)==6 for a in r.attempts))
        self.assertTrue(all(a.request_fingerprint and a.output_fingerprint for a in r.attempts))

    def test_oracle_is_not_passed_to_candidate(self):
        received=[]
        def candidate(request):
            self.assertIsInstance(request,DirectorRequest); self.assertFalse(hasattr(request,'narrative'))
            self.assertFalse(hasattr(request,'findings')); received.append(request.request_id)
            return controlled_director(request)
        self.assertTrue(self.run_suite(candidate).checks_passed); self.assertEqual(len(received),12)

    def test_caller_scores_or_pass_flags_are_not_accepted(self):
        r=self.run_suite(lambda _: {"passed":True,"score":1.0})
        self.assertFalse(r.checks_passed); self.assertEqual(r.passed_case_fraction,0)
        self.assertTrue(all(a.error_type=="ValueError" for a in r.attempts))

    def test_source_fact_error_detected_despite_unchanged_evidence_labels(self):
        def candidate(request):
            out=controlled_director(request)
            if request.request_id.endswith('triangle'):
                return respeak(out,("A triangle has four straight sides.",))
            return out
        r=self.run_suite(candidate); a=r.attempts[0]
        self.assertIn("NARRATIVE:sides",a.failed_checks); self.assertIn("NARRATIVE:wrong-sides",a.failed_checks)
        self.assertIsNone(a.error_type); self.assertFalse(r.checks_passed)
        self.assertEqual(dict(r.case_results)['rectangle'],True)

    def test_false_substring_does_not_satisfy_expected_word(self):
        case=self.suite.cases[0]
        expected=NarrativeExpectation('word-boundary','PRESENT',('side',),case.narrative[0].evidence_ids,'Test full lexical boundary')
        suite=replace(self.suite,cases=(replace(case,narrative=(expected,)),)+self.suite.cases[1:])
        r=self.run_suite(suite=suite)
        self.assertIn('NARRATIVE:word-boundary',r.attempts[0].failed_checks)

    def test_positive_order_and_parent_binding_uses_ped_order(self):
        r=self.run_suite(); out=r.attempts[-1].output
        self.assertIn('99',out.snapshot.segment_order[0]); self.assertIn('98',out.snapshot.segment_order[1])
        self.assertTrue(r.checks_passed)

    def test_reversed_narration_cannot_pass_by_preserving_parent_annotations(self):
        def candidate(request):
            out=controlled_director(request)
            if len(out.snapshot.utterances)>1:
                return respeak(out,tuple(u.text for u in out.snapshot.utterances),tuple(reversed(out.snapshot.segment_order)))
            return out
        r=self.run_suite(candidate); failures=r.attempts[-1].failed_checks
        self.assertIn('NARRATIVE:definition-before-effect',failures)
        self.assertTrue(any(f.startswith('UNEXPECTED_BLOCKER:') for f in failures))

    def test_missing_game_learning_model_cannot_be_hidden_by_video_success(self):
        def candidate(request):
            out=controlled_director(request)
            return replace(out,game_handoff=replace(out.game_handoff,concept_ids=('unrelated',)))
        r=self.run_suite(candidate)
        self.assertTrue(all('GAME_LEARNING_MODEL_BINDING' in a.failed_checks for a in r.attempts))
        self.assertEqual(r.passed_case_fraction,0)

    def test_blank_game_ids_rejected_despite_shallow_legacy_builder(self):
        def candidate(request):
            out=controlled_director(request); return replace(out,game_handoff=replace(out.game_handoff,mastery_checks=(' ',)))
        r=self.run_suite(candidate); self.assertTrue(all(a.error_type=='ValueError' for a in r.attempts))

    def test_candidate_exception_remains_in_denominator(self):
        def candidate(request):
            if request.request_id.endswith('triangle'): raise RuntimeError('private source string')
            return controlled_director(request)
        r=self.run_suite(candidate)
        self.assertEqual(len(r.case_results),6); self.assertAlmostEqual(r.passed_case_fraction,5/6)
        self.assertEqual(r.attempts[0].error_type,'RuntimeError'); self.assertNotIn('private source string',repr(r))
        self.assertEqual(r.qa_status,'BLOCKED')

    def test_inconsistent_replay_is_a_failure(self):
        calls={}
        def candidate(request):
            n=calls.get(request.request_id,0); calls[request.request_id]=n+1
            out=controlled_director(request)
            return replace(out,architecture=replace(out.architecture,title='one' if n%2 else 'two'))
        r=self.run_suite(candidate); self.assertEqual(len(r.unstable_cases),6); self.assertFalse(r.checks_passed)
        self.assertTrue(all(a.checks_passed for a in r.attempts))

    def test_equal_replay_produces_equal_report(self):
        self.assertEqual(self.run_suite(),self.run_suite())

    def test_missing_domain_or_empty_suite_rejected_before_execution(self):
        for suite in (replace(self.suite,cases=()),replace(self.suite,required_domains=self.suite.required_domains+('HISTORY',))):
            with self.assertRaises(ValueError): self.run_suite(suite=suite)

    def test_duplicate_case_and_request_identity_are_rejected(self):
        with self.assertRaises(ValueError): self.run_suite(suite=replace(self.suite,cases=self.suite.cases+(self.suite.cases[0],)))
        c=replace(self.suite.cases[1],request=self.suite.cases[0].request)
        with self.assertRaises(ValueError): self.run_suite(suite=replace(self.suite,cases=(self.suite.cases[0],c)+self.suite.cases[2:]))

    def test_source_bytes_tampering_missing_and_extra_are_rejected(self):
        wrong=replace(self.sources[0],data=b'changed source')
        for sources in ((wrong,)+self.sources[1:],self.sources[1:],self.sources+(SourceBytes('extra',b'x','text/plain'),)):
            with self.subTest(sources=sources),self.assertRaises(ValueError): self.run_suite(sources=sources)

    def test_changed_source_quotes_without_page_revision_are_rejected(self):
        c=self.suite.cases[0]; cat=c.request.catalog
        cat=replace(cat,passages=(replace(cat.passages[0],quote='invented source'),))
        suite=replace(self.suite,cases=(replace(c,request=replace(c.request,catalog=cat)),)+self.suite.cases[1:])
        with self.assertRaises(ValueError): self.run_suite(suite=suite)

    def test_stale_timing_fails_candidate_contract(self):
        def candidate(request):
            out=controlled_director(request); return replace(out,timeline=replace(out.timeline,scenes=()))
        r=self.run_suite(candidate); self.assertEqual(r.passed_case_fraction,0)
        self.assertTrue(all(a.error_type=='ValueError' for a in r.attempts))

    def test_ped_review_propagates_and_cannot_be_erased(self):
        c=self.suite.cases[0]; p=c.request.pedagogy
        decisions=tuple(replace(d,status='AMBIGUOUS',requires_review=True) for d in p.decisions)
        p=build_pedagogy_plan(plan_id=p.plan_id,source_id=p.source_id,objective_ids=p.objective_ids,lesson_ids=p.lesson_ids,decisions=decisions,policy_version=p.policy_version)
        suite=replace(self.suite,cases=(replace(c,request=replace(c.request,pedagogy=p)),)+self.suite.cases[1:])
        self.assertTrue(self.run_suite(suite=suite).checks_passed)
        def candidate(request):
            out=controlled_director(request); return replace(out,architecture=replace(out.architecture,requires_review=False))
        r=self.run_suite(candidate,suite=suite); self.assertIn('UPSTREAM_PED_REVIEW_DROPPED',r.attempts[0].failed_checks)

    def test_expected_negative_qa_case_is_distinct_from_qa_acceptance(self):
        c=self.suite.cases[0]
        c=replace(c,findings=(FindingExpectation('BIE-DIR-QA-006','REQUIRED_REFLECTION_SHORTFALL','BLOCKER',True),))
        suite=replace(self.suite,cases=(c,)+self.suite.cases[1:])
        def candidate(request):
            out=controlled_director(request)
            if request.request_id.endswith('triangle'): out=replace(out,pacing=(replace(out.pacing[0],minimum_reflection_ms=2000),))
            return out
        r=self.run_suite(candidate,suite=suite)
        self.assertTrue(r.checks_passed); self.assertEqual(r.qa_status,'BLOCKED'); self.assertFalse(r.accepted)

    def test_missing_expected_finding_fails(self):
        c=replace(self.suite.cases[0],findings=(FindingExpectation('BIE-DIR-QA-006','REQUIRED_REFLECTION_SHORTFALL','BLOCKER',True),))
        r=self.run_suite(suite=replace(self.suite,cases=(c,)+self.suite.cases[1:]))
        self.assertIn('FINDING:BIE-DIR-QA-006:REQUIRED_REFLECTION_SHORTFALL',r.attempts[0].failed_checks)

    def test_suites_cannot_self_declare_enterprise_acceptance_or_weaken_replay(self):
        with self.assertRaises(ValueError): self.run_suite(suite=replace(self.suite,provenance='ACCEPTED_ENTERPRISE'))
        for count in (1,True,2.5):
            with self.assertRaises(ValueError): self.run_suite(repetitions=count)

    def test_oracle_and_pacing_policy_change_invalidate_suite_identity(self):
        c=self.suite.cases[0]; changed=replace(c,narrative=(replace(c.narrative[0],phrases=('different expectation',)),))
        a=self.run_suite(); b=self.run_suite(suite=replace(self.suite,cases=(changed,)+self.suite.cases[1:]))
        self.assertNotEqual(a.suite_fingerprint,b.suite_fingerprint)
        self.assertNotEqual(self.suite.fingerprint(),replace(self.suite,pacing_policy=replace(self.suite.pacing_policy,maximum_wpm=190)).fingerprint())


if __name__=='__main__': unittest.main()
