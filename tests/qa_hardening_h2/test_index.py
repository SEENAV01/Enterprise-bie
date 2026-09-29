"""Authored local file/receipt controls. Synthetic receipts are NOT production evidence."""
from h2_support import *
from copy import deepcopy
from bie.qa.governance_v2.index import *
from bie.qa.governance_v2.catalog import ORIGINAL_TASK_MAP,ORIGINAL_NAMESPACES,HARDENING_TASK_IDS

class Metadata(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        self.suites=[('mini','tests/mini',1)];self.receipt='run/TEST_RESULT.json'
        def put(p,data):
            path=self.root/p;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data if type(data)is bytes else canonical_bytes(data))
        self.put=put
        names=list(ORIGINAL_NAMESPACES)+['bie/qa/governance_v2']
        for ns in names:put(ns+'/entry.py',b'def evaluate():\n    return False\n')
        put('docs/SPEC.md',b'SYNTHETIC specification');put('task/TASK_RESULT.json',{'synthetic':True})
        put('tests/mini/test_small.py',b'class Check:\n    def test_case(self):\n        pass\n')
        entries=[dict(task_id=tid,status='IMPLEMENTED_LOCAL_VERIFIED_PENDING_SECTION_REAUDIT' if i<6 else 'PLANNED_NOT_IMPLEMENTED',dependencies=[]) for i,tid in enumerate(HARDENING_TASK_IDS)]
        put('state.json',{'tasks':entries});latest=list(HARDENING_TASK_IDS[4:6])
        self.cont=dict(latest_checkpoint='SECTION16_HARDENING_H2',latest_task_ids=latest,hardening_tasks_with_local_implementation=6,batch_id='H2',github_integrated=False,product_accepted=False,full_section_complete=False)
        put('continuation.json',self.cont);put('result.json',dict(batch_id='H2',task_ids=latest))
        self.plan=dict(latest_checkpoint='SECTION16_HARDENING_H2',cumulative_source_namespaces=names,namespace_actions=[dict(namespace=n) for n in names],execute_automatically=False,all_preconditions_satisfied=False)
        put('plan.json',self.plan)
        self.bp=dict(schema_version='bie.qa.index-blueprint/1',checkpoint='SECTION16_HARDENING_H2',latest_task_ids=latest,namespaces=names,
            metadata_paths=dict(continuation='continuation.json',result='result.json',integration_plan='plan.json'),hardening_state_path='state.json',
            original_rows=[dict(task_id=k,original_capability=v[0],source_namespace=v[1],entrypoint=dict(path=v[1]+'/entry.py',symbol='evaluate'),spec=dict(path='docs/SPEC.md'),task_evidence_paths=['task/TASK_RESULT.json'],test_directory='tests/mini',shared_suite_name='mini') for k,v in ORIGINAL_TASK_MAP.items()],
            hardening_evidence={k:dict(source_paths=['bie/qa/governance_v2/entry.py'],specification='docs/SPEC.md',task_evidence=['task/TASK_RESULT.json'],suite_id='mini') for k in HARDENING_TASK_IDS[:6]})
        self.record=dict(passed=True,full_repository_regression=False,unique_suite_qualified_tests=1,
            code_hashes={n+'/entry.py':reference(self.root,n+'/entry.py')['sha256'] for n in names},
            test_hashes={'tests/mini/test_small.py':reference(self.root,'tests/mini/test_small.py')['sha256']},
            suites=[dict(suite='mini',path='tests/mini',run=1,success=True,failures=0,errors=0,skipped=0,test_ids=['test_small.Check.test_case'])])
        put(self.receipt,self.record)
    def build(self):return build_index(self.root,self.bp,receipt_path=self.receipt,suite_specs=self.suites)
    def fails(self,code):
        with self.assertRaises(ContractError)as cm:self.build()
        self.assertEqual(cm.exception.code,code)
    def test_complete_index(self):
        d=self.build();self.assertEqual(len(d['original_tasks']),76);self.assertEqual(len(d['namespaces']),23);self.assertEqual(d['tests']['unique_tests'],1)
    def test_full_comparison(self):
        d=self.build();self.assertEqual(verify_index(self.root,d,self.bp,receipt_path=self.receipt,suite_specs=self.suites)['status'],'VERIFIED_LOCAL_INDEX')
    def test_deleted_index_row(self):
        d=self.build();d['original_tasks'].pop()
        with self.assertRaisesRegex(ContractError,'INDEX_CONTENT_MISMATCH'):verify_index(self.root,d,self.bp,receipt_path=self.receipt,suite_specs=self.suites)
    def test_original_missing(self):self.bp['original_rows'].pop();self.fails('INDEX_ORIGINAL_TASK_CENSUS')
    def test_original_duplicate(self):self.bp['original_rows'][0]=self.bp['original_rows'][1];self.fails('INDEX_ORIGINAL_TASK_CENSUS')
    def test_original_terminology_preserved(self):self.bp['original_rows'][0]['original_capability']='changed';self.fails('INDEX_TASK_BASELINE_CHANGED')
    def test_performance_namespace_required(self):self.bp['namespaces'].remove('bie/qa/performance_v2');self.fails('INDEX_BASELINE_NAMESPACE_MISSING')
    def test_publication_namespace_required(self):self.bp['namespaces'].remove('bie/qa/publication_v2');self.fails('INDEX_BASELINE_NAMESPACE_MISSING')
    def test_extra_namespace_detected(self):self.put('bie/qa/extra_v2/x.py',b'pass');self.fails('INDEX_NAMESPACE_CENSUS')
    def test_stale_source(self):self.put('bie/qa/release_v2/entry.py',b'pass');self.fails('INDEX_STALE_TEST_RECEIPT')
    def test_stale_test(self):self.put('tests/mini/test_small.py',b'pass');self.fails('INDEX_STALE_TEST_RECEIPT')
    def test_omitted_suite(self):self.record['suites']=[];self.put(self.receipt,self.record);self.fails('INDEX_SUITE_CENSUS')
    def test_omitted_test(self):self.record['suites'][0]['test_ids']=[];self.put(self.receipt,self.record);self.fails('INDEX_TEST_CENSUS')
    def test_failed_test_receipt(self):self.record['passed']=False;self.put(self.receipt,self.record);self.fails('INDEX_RECEIPT_NOT_LOCAL_PASS')
    def test_skipped_suite(self):self.record['suites'][0]['skipped']=1;self.put(self.receipt,self.record);self.fails('INDEX_SUITE_RESULT')
    def test_receipt_wrong_count(self):self.record['unique_suite_qualified_tests']=99;self.put(self.receipt,self.record);self.fails('INDEX_TEST_TOTAL')
    def test_suite_path_identity(self):self.record['suites'][0]['path']='elsewhere';self.put(self.receipt,self.record);self.fails('INDEX_SUITE_RESULT')
    def test_source_path_in_identity(self):self.assertIn('::tests/mini/test_small.py::',self.build()['tests']['tests'][0]['qualified_id'])
    def test_missing_spec(self):(self.root/'docs/SPEC.md').unlink();self.fails('INDEX_MISSING_FILE')
    def test_missing_evidence(self):(self.root/'task/TASK_RESULT.json').unlink();self.fails('INDEX_MISSING_FILE')
    def test_symbol_required(self):self.bp['original_rows'][0]['entrypoint']['symbol']='unknown';self.fails('INDEX_SYMBOL_NOT_UNIQUE')
    def test_stale_latest_checkpoint(self):self.cont['latest_checkpoint']='old';self.put('continuation.json',self.cont);self.fails('INDEX_STALE_CONTINUATION')
    def test_stale_latest_task(self):self.cont['latest_task_ids']=['wrong'];self.put('continuation.json',self.cont);self.fails('INDEX_STALE_CONTINUATION')
    def test_stale_result(self):self.put('result.json',dict(batch_id='OLD',task_ids=[]));self.fails('INDEX_STALE_RESULT')
    def test_stale_integration_plan(self):self.plan['latest_checkpoint']='old';self.put('plan.json',self.plan);self.fails('INDEX_STALE_INTEGRATION_PLAN')
    def test_missing_integration_action(self):self.plan['namespace_actions'].pop();self.put('plan.json',self.plan);self.fails('INDEX_INTEGRATION_ACTION_CENSUS')
    def test_auto_write_not_authorized(self):self.plan['execute_automatically']=True;self.put('plan.json',self.plan);self.fails('INDEX_UNSUPPORTED_INTEGRATION_CLAIM')
    def test_false_acceptance_rejected(self):self.cont['product_accepted']=True;self.put('continuation.json',self.cont);self.fails('INDEX_UNSUPPORTED_ACCEPTANCE_CLAIM')
    def test_missing_hardening_evidence(self):self.bp['hardening_evidence'].pop(HARDENING_TASK_IDS[0]);self.fails('INDEX_HARDENING_EVIDENCE_CENSUS')
    def test_index_no_product(self):self.assertFalse(self.build()['product_accepted'])
    def test_path_traversal_denied(self):
        with self.assertRaises(ContractError):read_file(self.root,'../secret')
    def test_absolute_path_denied(self):
        with self.assertRaises(ContractError):read_file(self.root,'/etc/passwd')
    def test_symlink_denied(self):
        (self.root/'linked').symlink_to(self.root/'docs/SPEC.md')
        with self.assertRaisesRegex(ContractError,'INDEX_SYMLINK'):read_file(self.root,'linked')
    def test_nonregular_denied(self):
        with self.assertRaises(ContractError):read_file(self.root,'docs')
