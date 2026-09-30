import unittest
from copy import deepcopy
from bie.evaluation.benchmarks.models import BenchmarkError,digest
from bie.evaluation.benchmarks.release.domains import evaluate
class DomainMinimums003(unittest.TestCase):
    def setUp(self):
        self.p={'id':'domains','domains':[{'id':'physics','minimum_score':'4/5','minimum_cases':2,'minimum_measured_fraction':'1'},
                                        {'id':'math','minimum_score':'1','minimum_cases':1,'minimum_measured_fraction':'1'}]}
        self.roster=[{'id':'a','domain':'physics','leakage_group':'g1','weight':'1'},
                     {'id':'b','domain':'physics','leakage_group':'g2','weight':'1'},
                     {'id':'c','domain':'math','leakage_group':'g3','weight':'1'}]
        self.rows=[{'id':r['id'],'status':'MEASURED','score':'1'} for r in self.roster]
    def run_gate(self,pin=None):return evaluate(self.p,self.roster,self.rows,expected_policy_sha256=digest(self.p) if pin is None else pin)
    def test_all_domain_minima_pass(self):self.assertEqual('PASS',self.run_gate()['outcome'])
    def test_one_domain_failure_not_masked(self):self.rows[2]['score']='1/2';self.assertEqual('FAIL',self.run_gate()['outcome'])
    def test_missing_domain_case_keeps_denominator(self):
        self.rows.pop(1);g={r['id']:r for r in self.run_gate()['domains']};self.assertEqual('1/2',g['physics']['score_exact'])
    def test_duplicate_leakage_groups_not_independent(self):
        self.roster[1]['leakage_group']='g1';self.assertIn('DOMAIN_INDEPENDENT_CASE_MINIMUM_NOT_MET',self.run_gate()['reasons'])
    def test_blocked_cases_do_not_count_as_independent(self):self.rows[1]['status']='BLOCKED';self.assertEqual('FAIL',self.run_gate()['outcome'])
    def test_unmeasured_fraction_minimum(self):self.rows.pop();self.assertIn('DOMAIN_COVERAGE_BELOW_MINIMUM',self.run_gate()['reasons'])
    def test_domain_policy_cannot_drop_weak_domain(self):
        self.p['domains'].pop()
        with self.assertRaisesRegex(BenchmarkError,'DOMAIN_POLICY_ROSTER_MISMATCH'):self.run_gate()
    def test_unconfigured_domain_rejects(self):
        self.roster[0]['domain']='chemistry'
        with self.assertRaises(BenchmarkError):self.run_gate()
    def test_unknown_result_rejects(self):
        self.rows.append({'id':'unknown','status':'MEASURED','score':'1'})
        with self.assertRaises(BenchmarkError):self.run_gate()
    def test_duplicate_case_rejects(self):
        self.roster.append(deepcopy(self.roster[0]))
        with self.assertRaises(BenchmarkError):self.run_gate()
    def test_weighted_domain_score_exact(self):
        self.roster[0]['weight']='3';self.rows[0]['score']='1/2';g={r['id']:r for r in self.run_gate()['domains']};self.assertEqual('5/8',g['physics']['score_exact'])
    def test_invalid_case_minimum_rejects(self):
        self.p['domains'][0]['minimum_cases']=True
        with self.assertRaises(BenchmarkError):self.run_gate()
    def test_empty_domain_roster_rejects(self):
        self.roster=[]
        with self.assertRaises(BenchmarkError):self.run_gate()
    def test_hash_pin_rejects(self):
        with self.assertRaises(BenchmarkError):self.run_gate(pin='0'*64)
    def test_domain_outputs_sorted(self):self.assertEqual(['math','physics'],[r['id'] for r in self.run_gate()['domains']])
    def test_no_product_acceptance(self):self.assertFalse(self.run_gate()['product_accepted'])
