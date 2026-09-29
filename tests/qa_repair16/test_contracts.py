from repair_helpers import *
from bie.qa.repair_v2.catalog import baseline_rules

class ContractTests(Fixture):
    def test_snapshot_codec_roundtrip(self):self.assertEqual(load_snapshot(canonical_bytes(asdict(self.snapshot))),self.snapshot)
    def test_batch_codec_roundtrip(self):self.assertEqual(load_batch(canonical_bytes(asdict(self.batch))),self.batch)
    def test_policy_codec_roundtrip(self):self.assertEqual(load_policy(canonical_bytes(asdict(self.policy))),self.policy)
    def test_proposal_codec_roundtrip(self):p=self.proposal();self.assertEqual(load_proposal(canonical_bytes(asdict(p))),p)
    def test_snapshot_order_invariant(self):self.assertEqual(replace(self.snapshot,artifacts=tuple(reversed(self.snapshot.artifacts))).content_digest,self.snapshot.content_digest)
    def test_run_identity_bound(self):self.assertNotEqual(replace(self.snapshot,run_id='different').content_digest,self.snapshot.content_digest)
    def test_revision_bound(self):self.assertNotEqual(replace(self.snapshot,revision='b'*40).content_digest,self.snapshot.content_digest)
    def test_policy_bounds_bound(self):self.assertNotEqual(replace(self.policy,max_attempts=2).content_digest,self.policy.content_digest)
    def test_default_catalog_no_automatic_environment(self):self.assertTrue(all(not r.automatic for r in baseline_rules() if r.category!='CONTENT'))
    def test_catalog_exact_pairs_unique(self):r=baseline_rules();self.assertEqual(len({(x.task_id,x.code) for x in r}),len(r))
    def test_effect_independent_of_proposal_id(self):p=self.proposal();self.assertEqual(replace(p,proposal_id='other').effect_digest,p.effect_digest)
    def test_effect_different_content(self):self.assertNotEqual(self.proposal(b'2+3').effect_digest,self.proposal(b'1+4',pid='other').effect_digest)
    def test_report_bound_adapter_bytes(self):b=self.batch.reports[0];self.assertEqual(b.artifact.sha256,hashlib.sha256((self.root/b.artifact.path).read_bytes()).hexdigest())
    def test_adapter_requires_real_report(self):self.assertRaises(ContractError,bind_report,{},'x','reports/x.json')
    def test_immutable_policy(self):
        with self.assertRaises(Exception):self.policy.max_attempts=99
    def test_immutable_snapshot(self):
        with self.assertRaises(Exception):self.snapshot.run_id='hijacked'

BAD_POLICY=[('zero_attempts','max_attempts',0),('bool_attempts','max_attempts',True),('unbounded_attempts','max_attempts',21),('negative_bytes','max_replacement_bytes',-1),('zero_total_bytes','max_total_replacement_bytes',0),('excess_file_budget','max_changed_files',65),('zero_timeout','worker_timeout_seconds',0),('unbounded_timeout','worker_timeout_seconds',61),('float_timeout','worker_timeout_seconds',1.5),('zero_age','max_receipt_age_seconds',0),('excess_age','max_receipt_age_seconds',604801),('zero_total_time','max_total_worker_seconds',0),('unknown_required','required_checks',('not-registered',)),('empty_required','required_checks',()),('duplicate_required','required_checks',('regression','regression')),('list_required','required_checks',['regression'])]
for name,key,value in BAD_POLICY:
    def test(self,k=key,v=value):self.assertRaises(ContractError,replace,self.policy,**{k:v})
    setattr(ContractTests,'test_reject_policy_'+name,test)

BAD_PATHS=['../source.txt','/tmp/x','generated/../x','generated//x','generated/.hidden','bie/qa/foo.py','tests/test.py','evidence/result.json','source/book.txt','policy/rules.json','task_registry/continuation.json','generated/C:x','generated/a\\b','generated/a\x00b']
for i,path in enumerate(BAD_PATHS):
    def test(self,p=path):self.assertRaises(ContractError,Replacement,p,'a'*64,self.snapshot.artifacts[1])
    setattr(ContractTests,f'test_reject_replacement_path_{i:02}',test)

class MoreContracts(Fixture):
    def test_duplicate_artifact_id(self):self.assertRaises(ContractError,replace,self.snapshot,artifacts=self.snapshot.artifacts+(self.snapshot.artifacts[0],))
    def test_invalid_revision(self):self.assertRaises(ContractError,replace,self.snapshot,revision='main')
    def test_unknown_owner(self):self.assertRaises(ContractError,FailureRule,'T','C','CONTENT','arbitrary',True)
    def test_environment_cannot_auto_repair(self):self.assertRaises(ContractError,FailureRule,'T','C','ENVIRONMENT','INFRA',True)
    def test_evidence_cannot_auto_repair(self):self.assertRaises(ContractError,FailureRule,'T','C','EVIDENCE','QA',True)
    def test_ambiguous_rule(self):self.assertRaises(ContractError,replace,self.policy,rules=self.policy.rules*2)
    def test_cyclic_checks(self):self.assertRaises(ContractError,replace,self.policy,checks=(CheckNode('syntax',('numeric',)),CheckNode('numeric',('syntax',)),CheckNode('regression',('numeric',))))
    def test_missing_dependency(self):self.assertRaises(ContractError,replace,self.policy,checks=(CheckNode('syntax',('absent',)),)+self.policy.checks[1:])
    def test_ambiguous_path_owners(self):self.assertRaises(ContractError,replace,self.policy,routes=self.policy.routes+(OwnerRoute('COMP',('generated/lesson.txt',),('syntax',)),))
    def test_missing_auto_owner(self):self.assertRaises(ContractError,replace,self.policy,rules=(FailureRule('T','C','CONTENT','COMP',True),))
    def test_empty_snapshot(self):self.assertRaises(ContractError,replace,self.snapshot,artifacts=())
    def test_duplicate_task_reports(self):self.assertRaises(ContractError,replace,self.batch,reports=self.batch.reports*2)
    def test_replacement_source_blob_rejected(self):self.assertRaises(ContractError,Replacement,'generated/lesson.txt','a'*64,self.snapshot.artifacts[0])
    def test_outcome_fail_needs_reason(self):self.assertRaises(ContractError,CheckOutcome,'syntax','a'*64,'b'*64,'FAIL',(),'c'*64)
    def test_outcome_skip_not_accepted_status(self):self.assertRaises(ContractError,CheckOutcome,'syntax','a'*64,'b'*64,'SKIP',(),'c'*64)
    def test_wire_extra_field(self):d=asdict(self.policy);d['trusted']=True;self.assertRaises(ContractError,load_policy,canonical_bytes(d))
    def test_wire_missing_field(self):d=asdict(self.policy);d.pop('rules');self.assertRaises(ContractError,load_policy,canonical_bytes(d))
    def test_wire_duplicate_key(self):self.assertRaises(ContractError,load_policy,b'{"x":1,"x":2}')
    def test_wire_nan(self):self.assertRaises(ContractError,load_policy,b'{"x":NaN}')
    def test_wire_float(self):self.assertRaises(ContractError,load_policy,b'{"x":0.5}')
    def test_wire_list_wrong_root(self):self.assertRaises(ContractError,load_policy,b'[]')
    def test_wire_bad_utf8(self):self.assertRaises(ContractError,load_policy,b'\xff')
