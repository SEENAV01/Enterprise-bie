"""Actual local registry/version/governance/ledger/domain interaction tests.

This is not the missing Section 16/real-book/native candidate integration.
"""
from copy import deepcopy
from helpers import Base,case
from bie.evaluation.benchmarks.models import canonical_json,digest
from bie.evaluation.benchmarks.registry import Registry
from bie.evaluation.benchmarks.versioning import VersionStore,Snapshot
from bie.evaluation.benchmarks.anti_gaming import AttemptLedger,leakage_report
from bie.evaluation.benchmarks.runner import PACK_MODULES,load_pack,reference_output
from bie.evaluation.benchmarks.session import grade_submission

class BatchIntegrationTests(Base):
    def setUp(self):
        super().setUp();self.cases=[c for task in PACK_MODULES for c in load_pack(task)]
        self.s=self.snapshot(self.cases);self.ledger=AttemptLedger(self.registry)
    def start(self):
        return self.ledger.start(run_id='local-run',campaign_id='local-development',candidate_sha256='c'*64,policy_sha256='d'*64,snapshot=self.s,split='DEVELOPMENT')
    def answers(self):return [{'case_id':c.case_id,'output':reference_output(c.task_id,c.inputs)} for c in self.s.cases]
    def test_full_60_case_pipeline_persists(self):
        self.start();r=grade_submission(self.ledger,'local-run',self.s,self.answers());self.assertEqual('PASS',r['report']['status']);self.assertEqual(len(self.cases),r['report']['denominator'])
        with Registry(self.root/'unit.sqlite3') as other:
            self.assertEqual(r['report'],AttemptLedger(other).get_report('local-run'));self.assertEqual(self.s,VersionStore(other).get('unit-dataset','1.0.0'));other.audit_head()
    def test_missing_case_is_failure_in_complete_denominator(self):
        self.start();r=grade_submission(self.ledger,'local-run',self.s,self.answers()[1:]);self.assertEqual('FAIL',r['report']['status']);self.assertEqual(len(self.cases),r['report']['denominator']);self.assertEqual((len(self.cases)-1)/len(self.cases),r['report']['score'])
    def test_mutated_scientific_value_fails_not_averaged_away(self):
        answers=self.answers();target=next(a for a in answers if a['case_id']=='BIE-EVAL-PHY-001.C001');target['output']['values']['force_N'][0]=-.009
        self.start();r=grade_submission(self.ledger,'local-run',self.s,answers);self.assertEqual('FAIL',r['report']['status']);self.assertEqual(len(self.cases)-1,r['report']['passed_count'])
    def test_candidate_pass_flag_is_not_a_score(self):
        answers=self.answers();answers[0]['output']={'status':'PASS','score':1};self.start();r=grade_submission(self.ledger,'local-run',self.s,answers);self.assertEqual('FAIL',r['report']['status'])
    def test_duplicate_output_rejected(self):
        answers=self.answers();answers[-1]=answers[0];self.start();self.code('DUPLICATE_ANSWER',grade_submission,self.ledger,'local-run',self.s,answers)
    def test_unknown_case_rejected(self):
        answers=self.answers();answers[0]['case_id']='not-registered';self.start();self.code('UNEXPECTED_CASE_RESULT',grade_submission,self.ledger,'local-run',self.s,answers)
    def test_changed_reference_snapshot_cannot_be_substituted(self):
        self.start();b=self.s.body;b['version']='1.0.1';other=Snapshot(canonical_json(b),digest(b));self.code('SUBMISSION_DATASET_MISMATCH',grade_submission,self.ledger,'local-run',other,self.answers())
    def test_readonly_public_views_no_answer_or_derivation(self):
        views=[c.candidate_view() for c in self.s.cases];self.assertEqual(len(self.cases),len(views));self.assertFalse(any('expected' in v or 'derivation' in v for v in views))
    def test_passing_reference_replay_not_native_acceptance(self):
        self.start();r=grade_submission(self.ledger,'local-run',self.s,self.answers());self.assertFalse(r['native_bie_execution_verified']);self.assertFalse(r['golden_benchmark_certified']);self.assertFalse(r['product_accepted'])
    def test_second_submission_rejected(self):
        self.start();grade_submission(self.ledger,'local-run',self.s,[]);self.code('RUN_ALREADY_CLOSED',grade_submission,self.ledger,'local-run',self.s,self.answers())
    def test_independent_database_same_snapshot_hash(self):
        with Registry(self.root/'independent.sqlite3') as other:
            other.register(list(reversed(self.cases)));s=VersionStore(other).create('unit-dataset','1.0.0',[c.case_id for c in self.cases]);self.assertEqual(self.s.sha256,s.sha256)
    def test_complete_case_set_has_no_duplicate_problem_ids(self):
        self.assertEqual('CHECKED',leakage_report(self.s)['status']);self.assertEqual(len(self.cases),len({c.case_id for c in self.s.cases}))
