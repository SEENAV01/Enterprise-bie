from h4_support import *
class ReasonChecks(TempCase):
    def setUp(self):super().setUp();self.p,self.b,self.native,self.refs,self.d=reason_fixture(self.root)
    def run_it(self):return evaluate_reasoning(self.native,save(self.root,'reason.json',self.d),self.refs,self.root,self.b,self.p)[0]
    def repolicy(self,p):self.p=p;self.b=binding(p);self.d['binding']=asdict(self.b)
    def test_healthy_native_execution(self):self.assertEqual(self.run_it().status,'REVIEW_REQUIRED')
    def test_correlation_not_cause(self):self.repolicy(replace(self.p,causal_edges=(('force','motion','correlation'),)));self.blocked(self.run_it(),'CORRELATION_PROMOTED_TO_CAUSE')
    def test_unknown_cause_review(self):self.d['claims'][0]['cause']='unmeasured';self.assertIn('CAUSAL_MODEL_UNSUPPORTED',codes(self.run_it()))
    def test_reversed_chronology(self):self.d['claims'][1]['before']='second';self.d['claims'][1]['after']='first';self.blocked(self.run_it(),'CHRONOLOGY_COUNTEREXAMPLE')
    def test_overlapping_time_review(self):self.repolicy(replace(self.p,chronology=(('first','0','3'),('second','2','4'))));self.assertIn('CHRONOLOGY_INTERVAL_UNCERTAIN',codes(self.run_it()))
    def test_frame_counterexample(self):self.d['claims'][2]['left']['frame']='shifted';self.d['claims'][2]['right']['frame']='world';self.blocked(self.run_it(),'COORDINATE_FRAME_COUNTEREXAMPLE')
    def test_native_condition_loss(self):
        self.native=(replace(self.native[0],rationale_summary='It happens'),*self.native[1:]);self.d['native_digest']=native_digest([asdict(x)for x in self.native]);self.blocked(self.run_it(),'RE_CONDITION_OMITTED')
    def test_condition_source_required(self):
        self.repolicy(replace(self.p,conditions=(('cause','src','not actually stated'),)))
        with self.assertRaises(ContractError):self.run_it()
    def test_unknown_frame(self):
        self.d['claims'][2]['left']['frame']='unknown'
        with self.assertRaises(ContractError):self.run_it()
    def test_native_digest_tamper(self):
        self.d['native_digest']=digest('wrong')
        with self.assertRaises(ContractError):self.run_it()
    def test_missing_decision(self):
        self.d['claims'].pop()
        with self.assertRaises(ContractError):self.run_it()
    def test_duplicate_decision(self):
        self.d['claims'].append(self.d['claims'][0])
        with self.assertRaises(ContractError):self.run_it()
    def test_foreign_binding(self):
        self.d['binding']['revision']='b'*40
        with self.assertRaises(ContractError):self.run_it()
    def test_native_uncertainty_preserved(self):
        self.native=(replace(self.native[0],requires_review=True),*self.native[1:]);self.d['native_digest']=native_digest([asdict(x)for x in self.native]);self.assertIn('NATIVE_REASONING_REQUIRES_REVIEW',codes(self.run_it()))
    def test_unsupported_not_proof(self):self.d['claims'][2]=dict(decision_id='space',kind='counterfactual');self.assertIn('UNSUPPORTED_DOMAIN_REASONING',codes(self.run_it()))
    def test_frame_singular(self):
        with self.assertRaises(ContractError):replace(self.p,frames=(('bad','0','0','0','0','0','0'),))
    def test_native_evidence_unbound(self):
        self.native=(replace(self.native[0],evidence_refs=[EvidenceRef('absent','primary',0.9)]),*self.native[1:]);self.d['native_digest']=native_digest([asdict(x)for x in self.native])
        with self.assertRaises(ContractError):self.run_it()

class PedChecks(TempCase):
    def setUp(self):super().setUp();self.p,self.b,self.arch,self.cells,self.refs,self.d=pedagogy_fixture(self.root)
    def run_it(self):return evaluate_pedagogy(self.arch,self.cells,save(self.root,'ped.json',self.d),self.refs,self.root,self.b,self.p,now=NOW)[0]
    def test_healthy_not_mastery(self):self.assertEqual(self.run_it().status,'REVIEW_REQUIRED')
    def test_alternate_route_wrong(self):self.d['routes'][1]['scene_order']=['test','teach'];self.blocked(self.run_it(),'NONDEFAULT_ROUTE_MISMATCH')
    def test_native_transfer_deficit(self):
        self.cells=(replace(self.cells[0],transfer=False),);self.d['native_digest']=digest(dict(architecture=asdict(self.arch),cells=[asdict(c)for c in self.cells]));self.blocked(self.run_it(),'NATIVE_ASSESSMENT_REQUIREMENT_MISSING')
    def test_answer_leakage(self):self.d['routes'][0]['events'][0]['text']='The answer is four';self.blocked(self.run_it(),'OBSERVED_ANSWER_LEAKAGE')
    def test_early_feedback(self):self.d['routes'][0]['events'][1]['kind']='feedback';self.blocked(self.run_it(),'FEEDBACK_BEFORE_RESPONSE')
    def test_no_response_window(self):self.d['routes'][0]['events'][1]['at_ms']=5;self.blocked(self.run_it(),'RESPONSE_WINDOW_TOO_SHORT')
    def test_missing_assessment(self):self.d['routes'][0]['events']=self.d['routes'][0]['events'][:1];self.blocked(self.run_it(),'OBSERVED_ASSESSMENT_COVERAGE')
    def test_missing_remediation(self):self.d['routes'][0]['events'][1]['correct']=False;self.blocked(self.run_it(),'MISCONCEPTION_REMEDIATION_MISSING')
    def test_remediation_after_error(self):
        row=self.d['routes'][0];row['events'][1]['correct']=False;row['events'].append(dict(event_id='remedy',kind='remediation',item_id='item',scene_id='teach',at_ms=1700,text='Review the mechanism',correct=None));self.assertNotIn('MISCONCEPTION_REMEDIATION_MISSING',codes(self.run_it()))
    def test_missing_route(self):
        self.d['routes'].pop()
        with self.assertRaises(ContractError):self.run_it()
    def test_repeated_route(self):
        self.d['routes'][1]['route_id']='default'
        with self.assertRaises(ContractError):self.run_it()
    def test_trace_clock_reversal(self):
        self.d['routes'][0]['events'][2]['at_ms']=1
        with self.assertRaises(ContractError):self.run_it()
    def test_unbound_native(self):
        self.d['native_digest']=digest('different')
        with self.assertRaises(ContractError):self.run_it()
    def test_future_evidence(self):
        self.d['captured_at']=NOW+1
        with self.assertRaises(ContractError):self.run_it()
    def test_stale_evidence(self):
        self.d['captured_at']=NOW-90000
        with self.assertRaises(ContractError):self.run_it()
    def test_observed_label_not_proof(self):self.d['mode']='observed';self.assertIn('OBSERVED_RUNTIME_ATTESTATION_REQUIRED',codes(self.run_it()))
    def test_no_native_mutation(self):
        before=digest(asdict(self.arch));self.run_it();self.assertEqual(before,digest(asdict(self.arch)))

class DirectorChecks(TempCase):
    def setUp(self):super().setUp();self.p,self.b,self.native,self.refs,self.d=director_fixture(self.root)
    def run_it(self):return evaluate_director(self.native,save(self.root,'dir.json',self.d),self.refs,self.root,self.b,self.p,now=NOW)[0]
    def change_text(self,index,text):
        rows=list(self.native.segments);rows[index]=replace(rows[index],text_intent=text);self.native=replace(self.native,segments=tuple(rows));self.d['native_digest']=digest(asdict(self.native))
    def test_healthy_bilingual(self):self.assertEqual(self.run_it().status,'REVIEW_REQUIRED')
    def test_engaging_but_wrong(self):self.d['ratings']['academic']=0;self.blocked(self.run_it(),'RUBRIC_HARD_FLOOR_FAILED')
    def test_valid_but_unexplained(self):self.d['ratings']['explanation']=0;self.blocked(self.run_it(),'RUBRIC_HARD_FLOOR_FAILED')
    def test_missing_condition(self):self.change_text(1,'Velocity changes. बल');self.blocked(self.run_it(),'SOURCE_CONDITION_DROPPED')
    def test_missing_hindi_term(self):self.change_text(1,'Velocity changes when the net force is nonzero.');self.blocked(self.run_it(),'MULTILINGUAL_TERM_MISSING')
    def test_hidden_bidi_control(self):self.change_text(0,'Why?\u202e');self.blocked(self.run_it(),'SCRIPT_HIDDEN_CONTROL')
    def test_unexplained_hook(self):self.d['timeline'][1]['role']='recap';self.blocked(self.run_it(),'HOOK_WITHOUT_EXPLANATORY_PAYOFF')
    def test_early_payoff(self):self.d['timeline'][1]['start_ms']=100;self.blocked(self.run_it(),'HOOK_WITHOUT_EXPLANATORY_PAYOFF')
    def test_repeated_hook(self):self.change_text(1,self.native.segments[0].text_intent);self.blocked(self.run_it(),'REPEATED_HOOK_NOT_EXPLANATION')
    def test_timing_overflow(self):self.d['timeline'][1]['end_ms']=2001;self.blocked(self.run_it(),'MULTILINGUAL_TIMING_BUDGET')
    def test_missing_criterion(self):
        del self.d['ratings']['academic']
        with self.assertRaises(ContractError):self.run_it()
    def test_future_rating(self):
        self.d['rated_at']=NOW+1
        with self.assertRaises(ContractError):self.run_it()
    def test_unknown_language(self):
        self.d['timeline'][1]['language']='unknown'
        with self.assertRaises(ContractError):self.run_it()
    def test_score_bool(self):
        self.d['ratings']['academic']=True
        with self.assertRaises(ContractError):self.run_it()
    def test_native_changed_after_binding(self):
        self.d['native_digest']=digest('wrong')
        with self.assertRaises(ContractError):self.run_it()
    def test_stale_rating(self):
        self.d['rated_at']=NOW-999999
        with self.assertRaises(ContractError):self.run_it()
    def test_native_not_modified(self):before=digest(asdict(self.native));self.run_it();self.assertEqual(before,digest(asdict(self.native)))
