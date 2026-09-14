from dataclasses import replace
import json,tempfile,unittest
from input_fixtures import upstream
from annotation_fixtures import ANNOTATOR,AnnotationProtocolFixture,base_result
from bie.director.director_model import DirectingPolicy,DirectingFailure
from bie.director.narration_annotations import AnnotationPolicy,produce_annotations,verify_production
from bie.director.qa_contract import coverage


class AnnotationProductionTests(unittest.TestCase):
    def fixture(self,case='science'):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup);f=upstream(tmp.name,case);return f,base_result(f)
    def produce(self,f,b,p=None,**kwargs):return produce_annotations(f.io,f.inputs,b,p or AnnotationProtocolFixture(),ANNOTATOR,**kwargs)
    def reject(self,mutate,case='science'):
        f,b=self.fixture(case);p=AnnotationProtocolFixture(mutate)
        with self.assertRaises(DirectingFailure) as error:self.produce(f,b,p)
        self.assertEqual(error.exception.code,'RESPONSE_CONTRACT_REJECTED');self.assertEqual(len(p.requests),2)
        return error.exception

    def test_provider_produces_fine_claims_and_typed_revision_bound_records(self):
        f,b=self.fixture();p=AnnotationProtocolFixture();r=self.produce(f,b,p);a=r.annotations
        self.assertEqual(len(p.requests),1);self.assertGreater(len(a.claims),len(b.execution.claims))
        self.assertTrue(all(covered==total for uid,covered,total in coverage(b.execution.snapshot,a.claims)))
        self.assertEqual({d.utterance_id for d in a.discourse},set(b.execution.snapshot.segment_order))
        self.assertEqual(a.snapshot_fingerprint,b.execution.snapshot.fingerprint());self.assertTrue(a.emphasis)
        self.assertEqual(verify_production(r,f.inputs,b),a)

    def test_complete_source_and_actual_assessment_obligations_are_sent_as_data(self):
        f,b=self.fixture('history');p=AnnotationProtocolFixture();self.produce(f,b,p)
        payload=json.loads(p.requests[0].messages[1]['content'])
        self.assertEqual(payload['inputs']['source_pages'][0]['text'],f.inputs.catalog.pages[0].text)
        self.assertEqual(payload['inputs']['inferences'][0]['value']['linear_extension'],['A','B'])
        self.assertTrue(payload['assessment_bindings']);self.assertTrue(payload['complete_sentence_spans'])
        self.assertIn('untrusted DATA',p.requests[0].messages[0]['content'])

    def test_narration_or_source_edits_fail_before_provider_execution(self):
        for kind in ('narration','source'):
            f,b=self.fixture();p=AnnotationProtocolFixture()
            if kind=='narration':
                snapshot=replace(b.execution.snapshot,language='hi');b=replace(b,execution=replace(b.execution,snapshot=snapshot))
            else:
                root=next(x for x in f.io.load_graph(f.inputs.parent_refs).values() if x.artifact_type=='source.document')
                f.io.catalog.cas._path(root.payload['blob']['digest']).write_bytes(b'changed source')
            with self.subTest(kind=kind),self.assertRaises(ValueError):self.produce(f,b,p)
            self.assertEqual(p.requests,[])

    def test_stale_input_snapshot_or_plan_echo_is_rejected(self):
        for key in ('input_fingerprint','snapshot_fingerprint','plan_fingerprint'):
            def mutate(p,v,n):v[key]='sha256:'+'0'*64;return v
            with self.subTest(key=key):self.reject(mutate)

    def test_omitted_or_overlapping_claims_fail_coverage(self):
        for overlap in (False,True):
            def mutate(p,v,n):
                if overlap:v['claims'][1]['span']=v['claims'][0]['span']
                else:v['claims'].pop()
                return v
            with self.subTest(overlap=overlap):self.reject(mutate)

    def test_punctuation_and_quote_cannot_disappear_while_word_coverage_stays_full(self):
        def mutate(p,v,n):
            s=v['claims'][0]['span'];s['end_char']-=1;s['quote']=s['quote'][:-1];return v
        self.reject(mutate)
        def bad_quote(p,v,n):v['claims'][0]['span']['quote']='different text';return v
        self.reject(bad_quote)

    def test_partial_token_spans_and_boolean_offsets_are_rejected(self):
        for changed in (1,True):
            def mutate(p,v,n):v['claims'][0]['span']['start_char']=changed;return v
            with self.subTest(changed=changed):self.reject(mutate)

    def test_invented_evidence_or_concepts_cannot_attach_to_narration(self):
        def evidence(p,v,n):v['claims'][0]['evidence_ids']=['invented'];return v
        def concept(p,v,n):v['discourse'][0]['introduced_concepts']=['assumed-mastered'];return v
        self.reject(evidence);self.reject(concept)

    def test_assessment_opening_answer_and_response_time_are_mandatory(self):
        for kind in ('opening','answer','reflection','mode'):
            def mutate(p,v,n):
                item,q,a=p['assessment_bindings'][0]
                if kind in ('opening','answer'):
                    row=next(x for x in v['discourse'] if x['utterance_id']==(q if kind=='opening' else a))
                    row['opens_questions' if kind=='opening' else 'answers_questions']=[]
                else:
                    row=next(x for x in v['pacing'] if x['span']['utterance_id']==q)
                    row['minimum_reflection_ms' if kind=='reflection' else 'mode']=0 if kind=='reflection' else 'EXPLAIN'
                return v
            with self.subTest(kind=kind):self.reject(mutate)

    def test_missing_discourse_or_pacing_record_is_not_complete_annotation(self):
        for field in ('discourse','pacing'):
            def mutate(p,v,n):v[field].pop();return v
            with self.subTest(field=field):self.reject(mutate)

    def test_scene_boundary_must_be_annotated_or_explicitly_unresolved(self):
        self.reject(lambda p,v,n:{**v,'transitions':[]})
        f,b=self.fixture()
        def unresolved(p,v,n):v['transitions'][0].update(relation='UNRESOLVED',cue_span=None);return v
        r=self.produce(f,b,AnnotationProtocolFixture(unresolved))
        self.assertTrue(r.annotations.unresolved_transitions);self.assertEqual(r.annotations.transitions,())

    def test_definition_must_name_actual_term_and_use_matching_evidence(self):
        def mutate(p,v,n):v['terms'][0]['term']='word-not-in-narration';return v
        self.reject(mutate)

    def test_invalid_emphasis_strength_or_overlap_is_rejected(self):
        for strength in (True,float('nan'),1.1):
            def mutate(p,v,n):v['emphasis'][0]['strength']=strength;return v
            with self.subTest(strength=strength):self.reject(mutate)
        def overlap(p,v,n):v['emphasis'].append({**v['emphasis'][0],'anchor_id':'overlap'});return v
        self.reject(overlap)

    def test_model_cannot_set_age_grade_mastery_or_review_completion(self):
        for key in ('learner_age','grade','mastery','annotation_review_completed'):
            with self.subTest(key=key):self.reject(lambda p,v,n:{**v,key:True})

    def test_bounded_retry_preserves_grounded_payload_and_does_not_return_partial_record(self):
        f,b=self.fixture();p=AnnotationProtocolFixture(lambda p,v,n:'bad json' if n==1 else v);r=self.produce(f,b,p)
        self.assertEqual([a.outcome for a in r.attempts],['RESPONSE_CONTRACT_REJECTED','VALIDATED_OUTPUT'])
        self.assertEqual(p.requests[0].messages[1],p.requests[1].messages[1])
        self.assertNotEqual(p.requests[0].request_id,p.requests[1].request_id)

    def test_context_response_and_record_budgets_fail_without_truncation(self):
        policies=[(AnnotationPolicy(execution=DirectingPolicy(maximum_request_characters=20)),0),
                  (AnnotationPolicy(execution=DirectingPolicy(maximum_response_characters=20)),1),
                  (AnnotationPolicy(maximum_records=1),1)]
        for policy,calls in policies:
            f,b=self.fixture();p=AnnotationProtocolFixture()
            with self.subTest(policy=policy),self.assertRaises(DirectingFailure):self.produce(f,b,p,policy=policy)
            self.assertEqual(len(p.requests),calls)

    def test_refusal_and_wrong_identity_stop_without_retry(self):
        for change in ({'finish_reason':'refusal'},{'model':'other'}):
            class Provider(AnnotationProtocolFixture):
                def invoke(self,request):return replace(super().invoke(request),**change)
            f,b=self.fixture();p=Provider()
            with self.subTest(change=change),self.assertRaises(DirectingFailure):self.produce(f,b,p)
            self.assertEqual(len(p.requests),1)

    def test_materialized_annotation_edits_do_not_match_original_response(self):
        f,b=self.fixture();p=self.produce(f,b)
        altered=replace(p,annotations=replace(p.annotations,review_reasons=('invented',)))
        with self.assertRaisesRegex(ValueError,'edited'):verify_production(altered,f.inputs,b)


if __name__=='__main__':unittest.main()
