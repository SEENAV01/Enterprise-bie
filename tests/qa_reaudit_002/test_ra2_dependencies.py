from ra2_support import *
from bie.qa.assurance_quality_v2.harness import dependency_closure,STAGES,run_book

class RequiredInputs(h.Temp):
    def fixture(self):return h.pipeline_fixture(self.root,all_stages=True)
    def test_complete_chain_includes_all_qa_upstream(self):
        _,p,_=self.fixture();self.assertEqual(dependency_closure(p.steps)['QA'],STAGES[:13])
    def test_actual_qa_input_receives_every_ancestor_output(self):
        src,p,b=self.fixture();out=self.root/'out';r=run_book(src,out,p,b)
        self.assertEqual(len(r['details']['completed_stages']),15)
        self.assertEqual(r['report']['status'],'BLOCKED')
        self.assertFalse(r['details']['native_pipeline_executed'])
        for ancestor in STAGES[:13]:
            self.assertEqual((out/'QA-input/upstream'/ancestor/'data.txt').read_bytes(),b'DIAGNOSTIC')
        req=json.loads((out/'QA-input/book-request.json').read_text())
        self.assertEqual(tuple(x['stage'] for x in req['upstream']),STAGES[:13])
    def test_eval_receives_qa_and_all_native_outputs(self):
        _,p,_=self.fixture();self.assertEqual(dependency_closure(p.steps)['EVAL'],STAGES[:14])
    def test_dependency_not_registered(self):
        _,p,_=self.fixture();steps=(p.steps[0],p.steps[2])
        self.error('H39_DEPENDENCY_NOT_REGISTERED',replace,p,steps=steps)
    def test_redundant_direct_ancestors_do_not_duplicate_copy(self):
        _,p,_=self.fixture();steps=tuple(replace(s,dependencies=STAGES[:13]) if s.name=='QA' else s for s in p.steps)
        p=replace(p,steps=steps);self.assertEqual(len(dependency_closure(p.steps)['QA']),13)
    def test_partial_bi_ki_remains_explicitly_incomplete(self):
        src,p,b=h.pipeline_fixture(self.root);r=run_book(src,self.root/'out',p,b)
        self.assertEqual(r['details']['completed_stages'],['BI','KI']);self.assertEqual(r['report']['status'],'BLOCKED')
    def test_native_unprovisioned_still_executes_nothing(self):
        src,p,b=h.pipeline_fixture(self.root,profile='NATIVE');r=run_book(src,self.root/'out',p,b)
        self.assertEqual(r['details']['pipeline_records'],[])
    def test_required_ancestor_contract_cannot_be_replaced_in_request(self):
        _,p,_=self.fixture();self.assertFalse(hasattr(p,'required_ancestors'))

for name in STAGES[2:]:
    def missing(self,name=name):
        _,p,_=self.fixture();steps=tuple(replace(s,dependencies=('BI',)) if s.name==name else s for s in p.steps)
        self.error('H39_REQUIRED_DEPENDENCY_MISSING',replace,p,steps=steps)
    setattr(RequiredInputs,'test_'+name.lower()+'_cannot_skip_required_inputs',missing)
