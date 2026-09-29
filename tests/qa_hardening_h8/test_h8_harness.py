from h8_helpers import *
import threading

class Harness(Temp):
    def fixture(self,**kw):return pipeline_fixture(self.root,**kw)
    def test_real_processes_and_handoff(self):
        src,p,b=self.fixture();r=run_book(src,self.root/'out',p,b)
        self.assertEqual(r['details']['completed_stages'],['BI','KI']);self.assertFalse(r['details']['native_pipeline_executed']);self.assertEqual(r['report']['status'],'BLOCKED')
    def test_native_missing_profile_does_not_fallback(self):
        src,p,b=self.fixture(profile='NATIVE');r=run_book(src,self.root/'out',p,b);self.assertEqual(r['details']['pipeline_records'],[])
        self.assertIn('H8_NATIVE_EXECUTOR_NOT_PROVISIONED',[f['code'] for f in r['report']['findings']])
    def test_all_diagnostics_never_become_native(self):
        src,p,b=self.fixture(all_stages=True);r=run_book(src,self.root/'out',p,b);self.assertEqual(len(r['details']['completed_stages']),15);self.assertFalse(r['details']['native_pipeline_executed'])
    def test_mandatory_stage_census_cannot_shrink(self):
        src,p,b=self.fixture();self.error('H8_MANDATORY_STAGE_WAIVER',replace,p,required_stages=('BI','KI'))
    def test_duplicate_stage(self):
        src,p,b=self.fixture();self.error('H8_DUPLICATE_STAGE',replace,p,steps=(p.steps[0],p.steps[0]))
    def test_stage_order(self):
        src,p,b=self.fixture();self.error('H8_STAGE_ORDER',replace,p,steps=tuple(reversed(p.steps)))
    def test_future_dependency(self):
        src,p,b=self.fixture();s=replace(p.steps[0],dependencies=('EVAL',));self.error('H8_DEPENDENCY_ORDER',replace,p,steps=(s,p.steps[1]))
    def test_unknown_stage(self):
        src,p,b=self.fixture();self.error('H8_STEP_TYPE',replace,p.steps[0],name='FAKE')
    def test_missing_stage_receipt(self):
        src,p,b=self.fixture();s=replace(p.steps[0].stage,output_paths=('data.txt',));self.error('H8_STEP_RECEIPT_REQUIRED',replace,p.steps[0],stage=s)
    def test_changed_policy_binding(self):
        src,p,b=self.fixture();self.error('H8_BOOK_POLICY_BINDING',run_book,src,self.root/'out',p,replace(b,policy_digest='e'*64))
    def test_changed_source(self):
        src,p,b=self.fixture();(src/'source.txt').write_text('changed');self.error('H8_FILE_INVENTORY_CHANGED',run_book,src,self.root/'out',p,b)
    def test_source_candidate_binding(self):
        src,p,b=self.fixture();self.error('H8_BOOK_SOURCE_BINDING',run_book,src,self.root/'out',p,replace(b,candidate_digest='e'*64))
    def test_output_overlap(self):
        src,p,b=self.fixture();self.error('H8_BOOK_OUTPUT_OVERLAP',run_book,src,src/'out',p,b)
    def test_output_no_overwrite(self):
        src,p,b=self.fixture();(self.root/'out').mkdir()
        with self.assertRaises(FileExistsError):run_book(src,self.root/'out',p,b)
    def test_actual_failed_check(self):
        src,p,b=self.fixture(bad="v['checks'][0]['status']='FAIL';(o/'qa-result.json').write_text(json.dumps(v))")
        r=run_book(src,self.root/'out',p,b);self.assertEqual(r['details']['completed_stages'],['BI']);self.assertIn('H8_STAGE_CHECK_FAILED',json.dumps(r))
    def test_replayed_execution_id(self):
        src,p,b=self.fixture(bad="v['execution_id']='old';(o/'qa-result.json').write_text(json.dumps(v))")
        r=run_book(src,self.root/'out',p,b);self.assertIn('H8_STAGE_RECEIPT_BINDING',json.dumps(r))
    def test_source_loss_binding(self):
        src,p,b=self.fixture(bad="v['source_digest']='0'*64;(o/'qa-result.json').write_text(json.dumps(v))")
        r=run_book(src,self.root/'out',p,b);self.assertIn('H8_STAGE_RECEIPT_BINDING',json.dumps(r))
    def test_missing_case(self):
        src,p,b=self.fixture(bad="v['checks']=[];(o/'qa-result.json').write_text(json.dumps(v))")
        r=run_book(src,self.root/'out',p,b);self.assertIn('H8_CHECK_CENSUS',json.dumps(r))
    def test_extra_output(self):
        src,p,b=self.fixture(bad="(o/'extra.txt').write_text('extra')")
        r=run_book(src,self.root/'out',p,b);self.assertIn('H8_STAGE_OUTPUT_CENSUS',json.dumps(r))
    def test_golden_mismatch(self):
        src,p,b=self.fixture();s=replace(p.steps[0],golden_outputs=({'path':'data.txt','sha256':'f'*64,'bytes':10},));p=replace(p,steps=(s,p.steps[1]));b=replace(b,policy_digest=p.content_digest)
        r=run_book(src,self.root/'out',p,b);self.assertIn('H8_GOLDEN_MISMATCH',json.dumps(r))
    def test_producer_changed_after_registration(self):
        src,p,b=self.fixture();Path(p.steps[0].stage.program.script_path).write_text('changed');r=run_book(src,self.root/'out',p,b);self.assertIn('H7_PROGRAM_CHANGED',json.dumps(r))
    def test_source_unmodified(self):
        src,p,b=self.fixture();before=inventory(src);run_book(src,self.root/'out',p,b);self.assertEqual(inventory(src),before)
    def test_cancel_before_stage(self):
        src,p,b=self.fixture();c=threading.Event();c.set();r=run_book(src,self.root/'out',p,b,cancel=c);self.assertEqual(r['details']['pipeline_records'],[])
    def test_validator_generator_alias(self):
        src,p,b=self.fixture(all_stages=True);steps=list(p.steps);steps[-1]=replace(steps[-1],stage=replace(steps[-1].stage,program=steps[0].stage.program))
        self.error('H8_VALIDATOR_GENERATOR_ALIAS',replace,p,steps=tuple(steps))
    def test_stage_status_skipped_rejected(self):
        src,p,b=self.fixture(bad="v['checks'][0]['status']='SKIPPED';(o/'qa-result.json').write_text(json.dumps(v))")
        r=run_book(src,self.root/'out',p,b);self.assertIn('H8_STAGE_CHECK_FAILED',json.dumps(r))
    def test_missing_lineage_dependency(self):
        src,p,b=self.fixture();s=replace(p.steps[1],dependencies=());self.error('H8_SOURCE_LINEAGE_MISSING',replace,p,steps=(p.steps[0],s))
    def test_reserved_source_path(self):
        src,p,b=self.fixture();(src/'book-request.json').write_text('{}');p=replace(p,source_rows=tuple(inventory(src)));b=replace(b,policy_digest=p.content_digest,candidate_digest=digest(inventory(src)))
        self.error('H8_RESERVED_SOURCE_PATH',run_book,src,self.root/'out',p,b)
