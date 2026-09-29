from h7_helpers import *

class Reproduction(Temp):
    def setUp(self):
        super().setUp();self.src=self.root/'input';self.dep,self.review=dependency_fixture(self.src)
        self.tools=(('python',str(Path(sys.executable).resolve())),)
        self.policy=ReproductionPolicy(self.dep,host_profile(self.tools),self.tools,('answer.txt',))
        self.prog=make_program(self.root/'tool.py',"import os\nfrom pathlib import Path\ni=Path(os.environ['BIE_INPUT_ROOT']);o=Path(os.environ['BIE_OUTPUT_ROOT']);(o/'answer.txt').write_bytes((i/'package/value.txt').read_bytes())\n")
    def call(self,policy=None,prog=None,review=None):
        r=review or self.review
        return reproduce(self.src,self.root/'runs',prog or self.prog,policy or self.policy,r,approved_review_digest=digest(r),now=NOW)
    def test_actual_two_restores(self):
        r=self.call();self.assertEqual(r['status'],'REVIEW_REQUIRED');self.assertEqual(len(r['runs']),2)
        self.assertEqual(len({x['execution_id'] for x in r['runs']}),2);self.assertEqual(len({x['output_digest'] for x in r['runs']}),1)
        self.assertFalse(r['full_os_image_rebuilt']);self.assertFalse(r['product_accepted'])
    def test_source_preserved(self):
        before=inventory(self.src);self.call();self.assertEqual(before,inventory(self.src))
    def test_host_drift(self):
        p=replace(self.policy,host={**self.policy.host,'kernel':'wrong'})
        self.error('H7_HOST_DRIFT',self.call,p)
        self.assertFalse((self.root/'runs').exists())
    def test_cross_host_missing(self):
        r=self.call(replace(self.policy,cross_host_required=True));self.assertEqual(r['status'],'BLOCKED');self.assertIn('H7_CROSS_HOST_EVIDENCE_MISSING',r['errors'])
    def test_nondeterministic(self):
        p=make_program(self.root/'random.py',"import os\nfrom pathlib import Path\n(Path(os.environ['BIE_OUTPUT_ROOT'])/'answer.txt').write_bytes(os.urandom(32))")
        self.assertIn('H7_REPRO_NONDETERMINISTIC',self.call(prog=p)['errors'])
    def test_failed_producer(self):
        p=make_program(self.root/'fail.py','raise RuntimeError("injected failure")')
        self.assertIn('H7_REPRO_EXECUTION_FAILED',self.call(prog=p)['errors'])
    def test_missing_output(self):
        p=make_program(self.root/'empty.py','pass')
        self.assertIn('H7_REPRO_OUTPUT_CENSUS',self.call(prog=p)['errors'])
    def test_extra_output(self):
        p=make_program(self.root/'extra.py',"import os\nfrom pathlib import Path\no=Path(os.environ['BIE_OUTPUT_ROOT']);(o/'answer.txt').write_text('42');(o/'extra').write_text('x')")
        self.assertIn('H7_REPRO_OUTPUT_CENSUS',self.call(prog=p)['errors'])
    def test_input_mutation(self):
        p=make_program(self.root/'edit.py',"import os\nfrom pathlib import Path\n(Path(os.environ['BIE_INPUT_ROOT'])/'package/value.txt').write_text('wrong')")
        self.assertIn('H7_REPRO_EXECUTION_FAILED',self.call(prog=p)['errors'])
        self.assertEqual((self.src/'package/value.txt').read_text(),'42')
    def test_dependency_block(self):
        r=json.loads(json.dumps(self.review));r['packages'][0].update(status='AFFECTED',advisory_ids=['DIAGNOSTIC-001'])
        self.error('H7_REPRO_DEPENDENCY_BLOCK',self.call,review=r)
    def test_empty_outputs(self):
        self.error('H7_REPRO_OUTPUTS',replace,self.policy,output_paths=())
    def test_duplicate_outputs(self):
        self.error('H7_REPRO_OUTPUTS',replace,self.policy,output_paths=('answer.txt','answer.txt'))
    def test_boolean_runs(self):
        with self.assertRaises(ContractError):replace(self.policy,required_runs=True)
    def test_excess_runs(self):
        with self.assertRaises(ContractError):replace(self.policy,required_runs=6)
    def test_tool_alias(self):self.error('H7_TOOL_ALIAS',host_profile,self.tools+self.tools)
    def test_no_overwrite(self):
        (self.root/'runs').mkdir()
        with self.assertRaises(FileExistsError):self.call()

class Rebuild(Temp):
    def setUp(self):
        super().setUp();self.src,self.change,self.scope,self.policy=build_fixture(self.root)
    def call(self,p=None,c=None,r=None):
        c=c or self.change
        return rebuild(c,self.scope,r or signed(c,self.scope),VERIFIER,NOW,self.src,self.root/'run',p or self.policy)
    def test_actual_pair(self):
        before=inventory(self.src);r=self.call();self.assertEqual(r['report']['status'],'REVIEW_REQUIRED')
        self.assertEqual(len([x for s in r['details']['sides'].values() for x in s['records']]),8)
        self.assertEqual(r['details']['sides']['baseline']['cases']['math'],'FAIL')
        self.assertEqual(r['details']['sides']['candidate']['cases']['math'],'PASS');self.assertEqual(before,inventory(self.src))
    def test_regressed_caption(self):
        c=make_change('BIE-QA-HARD-027',self.change.binding,self.src,self.change.target,canonical_bytes({'value':5,'caption':'wrong'}),self.scope,self.change.input_refs,{'synthetic':True})
        self.assertIn('H7_REPAIR_REGRESSION',[f['code'] for f in self.call(c=c)['report']['findings']])
    def test_native_required_cannot_promote(self):
        r=self.call(replace(self.policy,require_native=True));self.assertEqual(r['report']['status'],'BLOCKED');self.assertFalse(r['details']['native_rebuild_verified'])
    def test_wrong_repair(self):
        c=make_change('BIE-QA-HARD-027',self.change.binding,self.src,self.change.target,canonical_bytes({'value':6,'caption':'keep source condition'}),self.scope,self.change.input_refs,{'synthetic':True})
        self.assertFalse(self.call(c=c)['technical_checks_clear'])
    def test_target_not_reproduced(self):
        p=replace(self.policy,target_case_ids=('caption',));self.assertIn('H7_TARGET_NOT_REPRODUCED',[x['code'] for x in self.call(p)['report']['findings']])
    def test_unapproved_change(self):
        with self.assertRaises(ContractError):self.call(r=replace(signed(self.change,self.scope),signature='0'*64))
    def test_source_drift(self):
        (self.src/'source/book.txt').write_text('modified')
        with self.assertRaises(ContractError):self.call()
    def test_missing_case(self):
        p=replace(self.policy,expected_case_ids=('math','caption','missing'))
        self.error('H7_RESULT_CASE_CENSUS',self.call,p)
    def test_unexecuted_case(self):
        stage=self.policy.stages[-1];txt=Path(stage.program.script_path).read_text().replace("'PASS' if d['value']==5 else 'FAIL'","'SKIPPED'")
        prog=make_program(self.root/'skip.py',txt,name='regression');p=replace(self.policy,stages=self.policy.stages[:-1]+(replace(stage,program=prog),))
        self.error('H7_CASE_NOT_EXECUTED',self.call,p)
    def test_foreign_execution_id(self):
        stage=self.policy.stages[-1];txt=Path(stage.program.script_path).read_text().replace("os.environ['BIE_EXECUTION_ID']","'other-run'")
        p=replace(self.policy,stages=self.policy.stages[:-1]+(replace(stage,program=make_program(self.root/'foreign.py',txt)),))
        self.error('H7_REUSED_CAPTURE_ID',self.call,p)
    def test_partial_stage(self):
        p=replace(self.policy,stages=(replace(self.policy.stages[0],output_paths=('missing.json',)),)+self.policy.stages[1:])
        self.assertFalse(self.call(p)['technical_checks_clear'])
    def test_bad_stage_exit(self):
        p=replace(self.policy,stages=(replace(self.policy.stages[0],program=make_program(self.root/'error.py','raise SystemExit(4)')),)+self.policy.stages[1:])
        self.assertFalse(self.call(p)['technical_checks_clear'])
    def test_stage_order(self):self.error('H7_STAGE_ORDER',replace,self.policy,stages=tuple(reversed(self.policy.stages)))
    def test_stage_omission(self):self.error('H7_STAGE_CENSUS',replace,self.policy,stages=self.policy.stages[:-1])
    def test_unknown_target(self):self.error('H7_UNKNOWN_TARGET',replace,self.policy,target_case_ids=('missing',))
    def test_no_empty_targets(self):
        with self.assertRaises(ContractError):replace(self.policy,target_case_ids=())
    def test_new_captures_are_copied_to_later_stages(self):
        r=self.call();s=r['details']['sides']['candidate']['records'][-1]
        self.assertIn('upstream/capture/capture.json',{x['path'] for x in s['inputs']})
    def test_cannot_overwrite_original(self):
        before=inventory(self.src)
        with self.assertRaises(FileExistsError):rebuild(self.change,self.scope,signed(self.change,self.scope),VERIFIER,NOW,self.src,self.src,self.policy)
        self.assertEqual(before,inventory(self.src))
