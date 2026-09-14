from dataclasses import asdict,replace
import json,tempfile,unittest
from window_fixtures import long_upstream
from context_fixtures import context_upstream
from windowed_directing_fixtures import windowed_base,WindowProtocolFixture
from annotation_window_fixtures import production,WindowAnnotationFixture
from bie.director.narration_annotations import AnnotationPolicy,AnnotationProduction,verify_production
from bie.director.annotation_window_context import WindowedAnnotationPolicy,scene_view
from bie.director.director_model import DirectingFailure
from bie.director.director_artifacts import canonical
from bie.director.script_coherence_qa import coherence_qa


class AnnotationWindowTests(unittest.TestCase):
    def fixture(self,**kwargs):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        return long_upstream(tmp.name,**({'units':3,'page_characters':500}|kwargs))
    def base(self,f,provider=None):return windowed_base(f,provider)

    def test_previously_oversized_annotation_input_executes_with_every_spoken_word(self):
        f=self.fixture(units=8,page_characters=5600);b=self.base(f);old=WindowAnnotationFixture()
        with self.assertRaises(DirectingFailure):production(f,b,old,AnnotationPolicy())
        self.assertEqual(old.requests,[]);a=WindowAnnotationFixture();p=production(f,b,a)
        self.assertEqual(len(a.requests),9);self.assertEqual(len(p.annotations.discourse),len(b.execution.snapshot.utterances))
        self.assertEqual(verify_production(p,f.inputs,b),p.annotations)

    def test_each_source_view_keeps_full_pages_and_global_phase_keeps_all_exact_speech(self):
        f=self.fixture();b=self.base(f);a=WindowAnnotationFixture();production(f,b,a)
        payloads=[json.loads(r.messages[1]['content']) for r in a.requests];seen=set()
        pages={p.page_id:p.text for p in f.inputs.catalog.pages}
        for p in payloads[:-1]:
            for page in p['inputs']['source_pages']:
                self.assertEqual(page['text'],pages[page['page_id']]);self.assertTrue(page['text'].endswith(f.conditions[0]));seen.add(page['page_id'])
            for u in p['utterances']:
                full=next(x for x in b.execution.snapshot.utterances if x.utterance_id==u['utterance_id'])
                self.assertEqual(u['text'],full.text);self.assertEqual(p['original_utterance_fingerprints'][u['utterance_id']],full.fingerprint())
        self.assertEqual(seen,set(pages));global_data=payloads[-1]
        self.assertEqual([u['text'] for u in global_data['utterances']],[u.text for u in b.execution.snapshot.utterances])
        self.assertFalse(global_data['source_pages_in_this_request']);self.assertNotIn('source_pages',global_data['inputs'])

    def test_views_and_reconciliation_do_not_mutate_the_base_or_upstream_artifacts(self):
        f=self.fixture();b=self.base(f);before=canonical(asdict(b));count=len(f.io.catalog.records);production(f,b)
        self.assertEqual(before,canonical(asdict(b)));self.assertEqual(len(f.io.catalog.records),count)

    def test_local_ids_cannot_collide_across_scene_namespaces(self):
        f=self.fixture();b=self.base(f)
        def change(p,v,n):
            if p['operation']=='ANNOTATE_SCENE':v['claims'][0]['claim_id']='shared-id'
            return v
        a=WindowAnnotationFixture(change)
        with self.assertRaises(DirectingFailure):production(f,b,a)
        self.assertEqual(len(a.requests),2)

    def test_local_claim_coverage_cannot_omit_a_spoken_condition(self):
        f=self.fixture();b=self.base(f)
        def change(p,v,n):
            if p['operation']=='ANNOTATE_SCENE':v['claims'].pop()
            return v
        with self.assertRaises(DirectingFailure):production(f,b,WindowAnnotationFixture(change))

    def test_stale_local_scope_echo_is_rejected(self):
        f=self.fixture();b=self.base(f)
        def change(p,v,n):
            if p['operation']=='ANNOTATE_SCENE':v['scope_fingerprint']='stale'
            return v
        with self.assertRaises(DirectingFailure):production(f,b,WindowAnnotationFixture(change))

    def test_global_disclosure_cannot_omit_an_utterance(self):
        f=self.fixture();b=self.base(f)
        def change(p,v,n):
            if p['operation']=='RECONCILE_DISCOURSE':v['discourse'].pop()
            return v
        with self.assertRaises(DirectingFailure) as e:production(f,b,WindowAnnotationFixture(change))
        self.assertEqual(len(e.exception.attempts),5)

    def test_global_boundary_coverage_cannot_omit_a_transition(self):
        f=self.fixture();b=self.base(f)
        def change(p,v,n):
            if p['operation']=='RECONCILE_DISCOURSE':v['transitions'].pop()
            return v
        with self.assertRaises(DirectingFailure):production(f,b,WindowAnnotationFixture(change))

    def test_original_assessment_opening_and_feedback_ids_survive_global_reconciliation(self):
        f=self.fixture();b=self.base(f)
        def change(p,v,n):
            if p['operation']=='RECONCILE_DISCOURSE':
                next(r for r in v['discourse'] if r['answers_questions'])['answers_questions']=[]
            return v
        with self.assertRaises(DirectingFailure):production(f,b,WindowAnnotationFixture(change))

    def test_forward_reference_still_blocks_global_coherence_after_local_success(self):
        f=self.fixture();b=self.base(f)
        def change(p,v,n):
            if p['operation']=='RECONCILE_DISCOURSE':v['discourse'][0]['references']=[v['discourse'][-1]['utterance_id']]
            return v
        p=production(f,b,WindowAnnotationFixture(change));a=p.annotations
        q=coherence_qa(b.execution.snapshot,b.execution.architecture,a.discourse,a.transitions)
        self.assertEqual(q.status,'BLOCKED');self.assertIn('FORWARD_OR_UNKNOWN_REFERENCE',{f.code for f in q.findings})

    def test_distant_question_and_answer_use_actual_full_narration_and_global_ids(self):
        f=self.fixture()
        def speech(p,v,n):
            if p['operation']=='NARRATE_WINDOW':
                did=p['scene']['pedagogy_decision_ids'][0]
                if did.endswith(':1'):v['beats'][0]['text']+=' Why do these dates not establish a cause?'
                if did.endswith(':3'):v['beats'][0]['text']+=' The earlier question is answered by the source condition: dates establish order, not causation.'
            return v
        b=self.base(f,WindowProtocolFixture(speech));first=b.narrated_scenes[0].scene_id;last=b.narrated_scenes[-1].scene_id
        def links(p,v,n):
            if p['operation']=='RECONCILE_DISCOURSE':
                start=next(u['utterance_id'] for u in p['utterances'] if u['scene_id']==first)
                end=next(u['utterance_id'] for u in p['utterances'] if u['scene_id']==last)
                next(r for r in v['discourse'] if r['utterance_id']==start)['opens_questions'].append('question:dates')
                row=next(r for r in v['discourse'] if r['utterance_id']==end);row['answers_questions'].append('question:dates');row['references'].append(start)
            return v
        p=production(f,b,WindowAnnotationFixture(links));a=p.annotations
        q=coherence_qa(b.execution.snapshot,b.execution.architecture,a.discourse,a.transitions)
        self.assertFalse({'UNRESOLVED_QUESTION','ANSWER_WITHOUT_QUESTION','FORWARD_OR_UNKNOWN_REFERENCE'} & {x.code for x in q.findings})

    def test_global_phase_cannot_rewrite_local_claims(self):
        f=self.fixture();b=self.base(f)
        def change(p,v,n):
            if p['operation']=='RECONCILE_DISCOURSE':v['claims']=[]
            return v
        with self.assertRaises(DirectingFailure):production(f,b,WindowAnnotationFixture(change))

    def test_complete_global_speech_overflow_fails_without_truncation(self):
        f=self.fixture(units=8);b=self.base(f);a=WindowAnnotationFixture();production(f,b,a)
        sizes=[sum(len(m['content']) for m in r.messages)+len(canonical(r.response_schema)) for r in a.requests]
        limit=sizes[-1]-1024;self.assertGreater(limit,max(sizes[:-1]))
        policy=WindowedAnnotationPolicy();policy=replace(policy,execution=replace(policy.execution,maximum_request_characters=limit))
        limited=WindowAnnotationFixture()
        with self.assertRaises(DirectingFailure) as e:production(f,b,limited,policy)
        self.assertEqual(e.exception.code,'DIRECTOR_CONTEXT_BUDGET_EXCEEDED');self.assertEqual(len(limited.requests),8)

    def test_scene_window_budget_is_explicit_before_calls(self):
        f=self.fixture();b=self.base(f);a=WindowAnnotationFixture()
        with self.assertRaises(DirectingFailure) as e:production(f,b,a,WindowedAnnotationPolicy(maximum_windows=2))
        self.assertEqual(e.exception.code,'ANNOTATION_WINDOW_COUNT_EXCEEDED');self.assertFalse(a.requests)

    def test_policy_and_missing_or_edited_request_evidence_cannot_revalidate(self):
        f=self.fixture();b=self.base(f);p=production(f,b)
        bads=(replace(p,window_calls=p.window_calls[:-1]),replace(p,attempts=p.attempts[:-1]),
            replace(p,window_calls=(replace(p.window_calls[0],request_payload_fingerprint='changed'),)+p.window_calls[1:]),
            replace(p,annotations=replace(p.annotations,policy=replace(p.annotations.policy,maximum_windows=17))))
        for bad in bads:
            with self.subTest(bad=type(bad)),self.assertRaises(ValueError):verify_production(bad,f.inputs,b)
        stripped=AnnotationProduction(p.annotations,p.attempts,p.response_json,p.identity)
        with self.assertRaises(ValueError):verify_production(stripped,f.inputs,b)

    def test_corrected_retry_request_reconstructs_without_losing_previous_scenes(self):
        f=self.fixture();b=self.base(f);p=production(f,b,WindowAnnotationFixture(lambda p,v,n:{} if n==2 else v))
        self.assertEqual(len(p.attempts),5);verify_production(p,f.inputs,b)

    def test_supplied_math_steps_keep_operators_offsets_and_assessments(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup);f=context_upstream(tmp.name,'math');b=self.base(f)
        p=production(f,b);verify_production(p,f.inputs,b)
        self.assertEqual(len(p.window_calls),2)
        self.assertTrue(all(beat.mode=='DERIVE' for beat in p.annotations.pacing if 'beat' in beat.span.utterance_id))
        self.assertEqual(len(b.generated_assessment_bindings),1)

    def test_view_order_and_policy_are_validated(self):
        f=self.fixture();b=self.base(f);order=tuple(s.scene_id for s in b.plan.scenes)
        with self.assertRaises(ValueError):scene_view(f.inputs,b,tuple(reversed(order)))
        for changes in ({'maximum_windows':0},{'maximum_windows':True},{'window_version':'unknown'}):
            with self.assertRaises(ValueError):WindowedAnnotationPolicy(**changes).validate()


if __name__=='__main__':unittest.main()
