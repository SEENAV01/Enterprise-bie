from game_helpers import *
from bie.qa.game_v2.evaluator import oracle_paths

class EvaluationTests(FixtureCase):
    def test_healthy_synthetic_checks_pass(self):self.assertEqual(self.check().status,'CHECKS_PASSED')
    def test_unsigned_needs_review(self):self.assertEqual(evaluate(self.r,self.root,self.p,as_of=NOW).status,'REVIEW_REQUIRED')
    def test_all_four_tasks(self):self.assertEqual([r.task_id for r in self.check().reports],[f'BIE-QA-GAME-{i:03}' for i in range(1,5)])
    def test_finite_coverage(self):self.assertEqual(len(self.check().covered_transition_ids),14)
    def test_replays_count_not_learning_count(self):self.assertEqual(dict(self.check().reports[3].measurements)['observed_response_classes'],2)
    def test_repeat_deterministic_report(self):self.assertEqual(self.check().content_digest,self.check().content_digest)
    def test_parent_input_tamper(self):(self.root/self.r.inputs[0].path).write_bytes(b'corruption');self.assertEqual(self.check().status,'BLOCKED')
    def test_output_tamper(self):(self.root/self.r.outputs[1].path).write_bytes(b'corruption');self.assertEqual(self.check().status,'BLOCKED')
    def test_runtime_deleted(self):(self.root/self.r.runtime_receipt.path).unlink();self.assertEqual(self.check().status,'BLOCKED')
    def test_build_deleted(self):(self.root/self.r.build_receipt.path).unlink();self.assertEqual(self.check().status,'BLOCKED')
    def test_source_tamper(self):(self.root/self.r.source.sources[0].artifact.path).write_bytes(b'corruption');self.assertEqual(self.check().status,'BLOCKED')
    def test_screenshot_tamper(self):
        rr=load_runtime((self.root/self.r.runtime_receipt.path).read_bytes());(self.root/rr.traces[0].steps[0].screenshot.path).write_bytes(b'not PNG');self.assertEqual(self.check().status,'BLOCKED')
    def test_no_product_acceptance(self):self.assertFalse(self.check().to_dict()['native_game_acceptance']);self.assertFalse(self.check().to_dict()['learner_mastery_proven'])
    def test_input_scope(self):self.assertCode(self.check(p=replace(self.p,expected_input_digest='0'*64)),'GAME_INPUT_INVENTORY')
    def test_wrong_game(self):self.assertCode(self.check(r=replace(self.r,game_id='other')),'GAME_SCOPE_MISMATCH')
    def test_action_order(self):
        r=self.trace_change(lambda t:replace(t,steps=(t.steps[1],t.steps[0])+t.steps[2:]));self.assertCode(self.check(r),'GAME_ACTION_SEQUENCE')
    def test_missing_initial(self):self.assertCode(self.check(self.trace_change(lambda t:replace(t,steps=t.steps[1:]))),'GAME_ACTION_SEQUENCE')
    def test_clock_order(self):self.assertCode(self.check(self.step_change(lambda s:replace(s,start_ms=0),index=1)),'GAME_ACTION_CLOCK_ORDER')
    def test_action_latency(self):self.assertCode(self.check(self.step_change(lambda s:replace(s,end_ms=9000))),'GAME_ACTION_TIMEOUT')
    def test_failed_action(self):self.assertCode(self.check(self.step_change(lambda s:replace(s,succeeded=False))),'GAME_ACTION_FAILED')
    def test_error_action(self):self.assertCode(self.check(self.step_change(lambda s:replace(s,error='failed'))),'GAME_ACTION_FAILED')
    def test_missing_observable(self):self.assertCode(self.check(self.step_change(lambda s:replace(s,values=s.values[1:]))),'GAME_OBSERVABLE_COVERAGE')
    def test_hidden_state(self):self.assertCode(self.check(self.step_change(lambda s:replace(s,values=(replace(s.values[0],visible=False),)+s.values[1:]))),'GAME_HIDDEN_OR_AMBIGUOUS_STATE')
    def test_duplicate_dom(self):self.assertCode(self.check(self.step_change(lambda s:replace(s,values=(replace(s.values[0],count=2),)+s.values[1:]))),'GAME_HIDDEN_OR_AMBIGUOUS_STATE')
    def test_missing_dom(self):self.assertCode(self.check(self.step_change(lambda s:replace(s,values=(replace(s.values[0],count=0),)+s.values[1:]))),'GAME_HIDDEN_OR_AMBIGUOUS_STATE')
    def test_wrong_state(self):self.assertCode(self.check(self.step_change(lambda s:replace(s,values=(replace(s.values[0],text='99'),)+s.values[1:]))),'GAME_STATE_TRANSITION_MISMATCH')
    def test_divergent_replay(self):self.assertCode(self.check(self.step_change(lambda s:replace(s,values=(replace(s.values[0],text='99'),)+s.values[1:]))),'GAME_REPLAY_DIVERGENCE')
    def test_double_submit_score_inflation(self):
        def change(s):return replace(s,values=tuple(replace(v,text='20') if v.key=='score' else v for v in s.values))
        self.assertCode(self.check(self.step_change(change,index=4)),'GAME_STATE_TRANSITION_MISMATCH')
    def test_wrong_answer_reward(self):
        def change(s):return replace(s,values=tuple(replace(v,text='10') if v.key=='score' else v for v in s.values))
        self.assertCode(self.check(self.step_change(change,index=8)),'GAME_STATE_TRANSITION_MISMATCH')
    def test_viewport_change(self):self.assertCode(self.check(self.trace_change(lambda t:replace(t,width=t.width+1))),'GAME_VIEWPORT_SCOPE')
    def test_per_trace_modules(self):self.assertCode(self.check(self.trace_change(lambda t:replace(t,loaded_paths=(self.p.entrypoint,)))),'GAME_TRACE_LOADED_COVERAGE')
    def test_unseen_modules_in_trace(self):self.assertCode(self.check(self.trace_change(lambda t:replace(t,loaded_paths=t.loaded_paths+('evil.js',)))),'GAME_TRACE_LOADED_COVERAGE')
    def test_bad_screenshot_shape(self):self.assertCode(self.check(self.trace_change(lambda t:replace(t,width=320))),'GAME_SCREENSHOT_SHAPE')
    def test_bad_screenshot_format(self):
        a=artifact(self.root,'invalid.bin',b'INVALID IMAGE','invalid-image');self.assertCode(self.check(self.step_change(lambda s:replace(s,screenshot=a))),'GAME_SCREENSHOT_INVALID')
    def test_unmapped_claim(self):
        p=replace(self.p,text_bindings=self.p.text_bindings[:1]);self.assertCode(self.check(p=p),'GAME_LEARNING_CLAIM_SCOPE')
    def test_missing_claim(self):
        p=replace(self.p,learning=(replace(self.p.learning[0],correct_claim_id='nonexistent'),));self.assertCode(self.check(p=p),'GAME_LEARNING_CLAIM_MISSING')
    def test_hint_unmapped(self):
        p=replace(self.p,text_bindings=(replace(self.p.text_bindings[0],claim_id='unknown'),)+self.p.text_bindings[1:]);self.assertCode(self.check(p=p),'GAME_BOUND_CLAIM_MISSING')
    def test_required_hint_wrong_text(self):
        p=replace(self.p,text_bindings=(replace(self.p.text_bindings[0],claim_id='correct'),)+self.p.text_bindings[1:]);self.assertCode(self.check(p=p),'GAME_BOUND_TEXT_MISMATCH')

_BUILD_CASES=[('failed_exit',{'exit_code':1},'GAME_BUILD_EXECUTION_FAILED'),('not_started',{'started':False},'GAME_BUILD_EXECUTION_FAILED'),('timeout',{'timed_out':True},'GAME_BUILD_EXECUTION_FAILED'),('other_run',{'run_id':'other'},'GAME_BUILD_BINDING'),('other_revision',{'revision':'f'*40},'GAME_BUILD_BINDING'),('other_game',{'game_id':'other'},'GAME_BUILD_BINDING'),('old',{'issued_at':NOW-86401},'GAME_BUILD_STALE'),('future',{'issued_at':NOW+1},'GAME_BUILD_STALE'),('wrong_input',{'inputs_digest':'0'*64},'GAME_BUILD_ARTIFACT_LINK'),('wrong_output',{'outputs_digest':'0'*64},'GAME_BUILD_ARTIFACT_LINK'),('wrong_entry',{'entrypoint':'other.html'},'GAME_BUILD_ENTRYPOINT'),('wrong_tool',{'tool_id':'unapproved'},'GAME_BUILD_TOOL'),('diagnostic',{'execution_kind':'authored_diagnostic'},'GAME_NON_NATIVE_BUILD'),('reported',{'execution_kind':'reported'},'GAME_NON_NATIVE_BUILD')]
def build_case(ch,code):
    def f(self):self.assertCode(self.check(self.build(**ch)),code)
    return f
for name,ch,code in _BUILD_CASES:setattr(EvaluationTests,'test_build_'+name,build_case(ch,code))
_RUNTIME_CASES=[('other_run',{'run_id':'other'},'GAME_RUNTIME_BINDING'),('other_revision',{'revision':'f'*40},'GAME_RUNTIME_BINDING'),('other_game',{'game_id':'other'},'GAME_RUNTIME_BINDING'),('build_hash',{'build_receipt_sha256':'0'*64},'GAME_RUNTIME_ARTIFACT_LINK'),('outputs',{'outputs_digest':'0'*64},'GAME_RUNTIME_ARTIFACT_LINK'),('oracle',{'oracle_digest':'0'*64},'GAME_RUNTIME_ORACLE_LINK'),('expired',{'issued_at':NOW-86401},'GAME_RUNTIME_STALE'),('future',{'issued_at':NOW+1},'GAME_RUNTIME_STALE'),('predates',{'issued_at':NOW-30},'GAME_CAUSAL_TIME'),('injected',{'method':'injected_bundle'},'GAME_NOT_ENTRYPOINT_EXECUTION'),('about_blank',{'origin':'about:blank'},'GAME_NOT_ENTRYPOINT_EXECUTION'),('credentials',{'origin':'https://user:pass@example.org'},'GAME_NOT_ENTRYPOINT_EXECUTION'),('path',{'origin':'https://example.org/path'},'GAME_NOT_ENTRYPOINT_EXECUTION'),('query',{'origin':'https://example.org?secret=1'},'GAME_NOT_ENTRYPOINT_EXECUTION'),('fragment',{'origin':'https://example.org#x'},'GAME_NOT_ENTRYPOINT_EXECUTION'),('wrong_entry',{'entrypoint':'other.html'},'GAME_NOT_ENTRYPOINT_EXECUTION'),('diagnostic',{'execution_kind':'authored_diagnostic'},'GAME_NON_NATIVE_RUNTIME'),('sandbox',{'sandbox_verified':False},'GAME_SANDBOX_UNPROVEN'),('page_error',{'page_errors':('exception',)},'GAME_RUNTIME_EXCEPTION'),('console_error',{'console_errors':('error',)},'GAME_CONSOLE_ERROR'),('network',{'network_violations':('external',)},'GAME_NETWORK_VIOLATION'),('no_loaded',{'loaded':()},'GAME_REQUIRED_ASSET_NOT_LOADED'),('no_traces',{'traces':()},'GAME_TRACE_COVERAGE')]
def runtime_case(ch,code):
    def f(self):self.assertCode(self.check(self.runtime(**ch)),code)
    return f
for name,ch,code in _RUNTIME_CASES:setattr(EvaluationTests,'test_runtime_'+name,runtime_case(ch,code))

class MoreEvaluationTests(FixtureCase):
    def test_build_diagnostic_log(self):
        a=artifact(self.root,'build/error.json',encode_log(b'error TS1234: invalid source'),'error-log');self.assertCode(self.check(self.build(stdout=a)),'GAME_COMPILER_DIAGNOSTIC')
    def test_build_stderr_review(self):
        a=artifact(self.root,'build/warning.json',encode_log(b'warning'),'warning-log');self.assertCode(self.check(self.build(stderr=a)),'GAME_BUILD_STDERR')
    def test_log_forgery(self):
        a=artifact(self.root,'build/forged.json',b'{"encoding":"base64","data":"WA==","byte_count":1,"sha256":"invalid"}','forged-log');self.assertEqual(self.check(self.build(stdout=a)).status,'BLOCKED')
    def test_loaded_hash(self):
        rr=load_runtime((self.root/self.r.runtime_receipt.path).read_bytes());self.assertCode(self.check(self.runtime(loaded=(replace(rr.loaded[0],sha256='f'*64),)+rr.loaded[1:])),'GAME_LOADED_ASSET_MISMATCH')
    def test_one_replay_missing(self):
        rr=load_runtime((self.root/self.r.runtime_receipt.path).read_bytes());self.assertCode(self.check(self.runtime(traces=rr.traces[1:])),'GAME_TRACE_COVERAGE')
    def test_one_branch_cannot_hide_bad(self):
        r=self.step_change(lambda s:replace(s,succeeded=False),index=1,trace=4);self.assertEqual(self.check(r).status,'BLOCKED')
    def test_every_replay_must_be_valid(self):
        r=self.step_change(lambda s:replace(s,succeeded=False),index=1,trace=1);self.assertEqual(self.check(r).status,'BLOCKED')
    def test_hard_link_rejected(self):
        import os
        os.link(self.root/self.r.inputs[0].path,self.root/'alias');self.assertCode(self.check(),'HARD_LINK_REJECTED')
    def test_symlink_rejected(self):
        path=self.root/self.r.inputs[0].path;data=path.read_bytes();path.unlink();other=self.root/'other';other.write_bytes(data);path.symlink_to(other);self.assertEqual(self.check().status,'BLOCKED')
    def test_bound_text_not_observed(self):
        p=replace(self.p,text_bindings=(replace(self.p.text_bindings[0],state_ids=('win',)),)+self.p.text_bindings[1:]);self.assertCode(self.check(p=p),'GAME_BOUND_TEXT_MISMATCH')
    def test_finite_oracle_all_paths(self):self.assertEqual(set(oracle_paths(self.p)),{'pointer','keyboard','mobile'})
    def test_undefined_oracle_action(self):
        p=replace(self.p,scenarios=(replace(self.p.scenarios[0],action_ids=('decrease',)),)+self.p.scenarios[1:]);self.assertRaises(ContractError,oracle_paths,p)
    def test_oracle_coverage_omitted(self):self.assertRaises(ContractError,oracle_paths,replace(self.p,scenarios=self.p.scenarios[:1]))
    def test_oracle_unreachable(self):
        s=State('never',(Value('x','99'),)+self.p.states[0].values[1:],False,False);self.assertRaises(ContractError,oracle_paths,replace(self.p,states=self.p.states+(s,)))
    def test_failures_do_not_get_coverage(self):
        rr=load_runtime((self.root/self.r.runtime_receipt.path).read_bytes());rr=replace(rr,traces=tuple(replace(t,steps=tuple(replace(s,succeeded=False) for s in t.steps)) for t in rr.traces));self.assertCode(self.check(self.runtime(traces=rr.traces)),'GAME_OBSERVED_TRANSITION_COVERAGE')
