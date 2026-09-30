from copy import deepcopy
import json,unittest
from pathlib import Path
from bie.evaluation.benchmarks.metrics import evaluate
from bie.evaluation.benchmarks.models import BenchmarkError,digest
ROOT=Path(__file__).resolve().parents[2]
def fixture(task):return json.loads((ROOT/'bie/evaluation/benchmarks/metrics/fixtures'/f'{task}.json').read_text())
def args(f,index=0):
    r=f['reference'];case=f['cases'][index];c=case['candidate'];a=case.get('source_artifacts',f['source_artifacts'])
    return dict(metric_id=r['metric_id'],reference=r,candidate=c,expected_reference_sha256=digest(r),expected_candidate_sha256=digest(c),source_artifacts=a)
class DeliveryMetricBase(unittest.TestCase):
    task=None
    def example(self):
        f=fixture(self.task);return f['reference'],f['cases'][0]['candidate'],f['source_artifacts']
    def measure(self,r=None,c=None,a=None):
        rr,cc,aa=self.example();r=rr if r is None else r;c=cc if c is None else c;a=aa if a is None else a
        return evaluate(self.task,r,c,expected_reference_sha256=digest(r),expected_candidate_sha256=digest(c),source_artifacts=a)
    def reject(self,r=None,c=None,a=None,code=None):
        with self.assertRaises(BenchmarkError) as ctx:self.measure(r,c,a)
        if code:self.assertEqual(code,ctx.exception.code)
        return ctx.exception.code
    def fail_reason(self,r,c,a,reason):
        o=self.measure(r,c,a);self.assertEqual('FAIL',o['outcome']);self.assertIn(reason,{d['reason'] for d in o['defects']});return o

def attach(cls):
    # Each fixture is a separately named observed positive or negative contract.
    for i in range(6):
        def check(self,i=i):
            f=fixture(self.task);case=f['cases'][i]
            if case['expected_status']=='BLOCKED':
                with self.assertRaises(BenchmarkError) as err:evaluate(**args(f,i))
                self.assertEqual(case['expected_reason'],err.exception.code)
            else:
                o=evaluate(**args(f,i));self.assertEqual(case['expected_outcome'],o['outcome']);self.assertEqual(case['expected_score_exact'],o['score_exact'])
                if case['expected_reason']:self.assertIn(case['expected_reason'],{d['reason'] for d in o['defects']})
                self.assertIs(False,o['release_authorized']);self.assertIs(False,o['product_accepted'])
        setattr(cls,f'test_authored_contract_{i+1:03d}',check)
    return cls
