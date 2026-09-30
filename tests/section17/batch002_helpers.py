"""Shared authored-fixture tests; subtests are never counted as extra methods."""
from copy import deepcopy
import unittest
from bie.evaluation.benchmarks.models import BenchmarkError
from bie.evaluation.benchmarks.runner import load_pack, reference_output, grade_case

def q(value,unit):return {'value':value,'unit':unit}
def date(year,month=None,day=None,era='CE'):
    d={'year':year,'era':era,'precision':'day' if day is not None else 'month' if month is not None else 'year','calendar':'proleptic_gregorian'}
    if month is not None:d['month']=month
    if day is not None:d['day']=day
    return d

class Batch002Base(unittest.TestCase):
    task=None
    def cases(self):return load_pack(self.task)
    def input(self,index=0):return deepcopy(self.cases()[index].inputs)
    def result(self,data):return reference_output(self.task,data)
    def values(self,data):
        out=self.result(data);self.assertEqual('OK',out['status'],out);return out['values']
    def rejected(self,data,code=None):
        out=self.result(data);self.assertEqual('REJECTED',out['status'],out)
        if code:self.assertEqual(code,out['error_code'])
    def error(self,code,fn,*args):
        with self.assertRaises(BenchmarkError) as ctx:fn(*args)
        self.assertEqual(code,ctx.exception.code)


def attach_fixture_tests(cls):
    # Each method replays a separately authored case, not solver-generated answers.
    for index in range(12):
        def test(self,index=index):
            cases=self.cases();self.assertEqual(12,len(cases));case=cases[index]
            self.assertEqual('DEVELOPMENT',case.split)
            self.assertEqual('AUTHORED_DIAGNOSTIC',case.evidence_grade)
            self.assertEqual(case.expected,reference_output(self.task,case.inputs))
            self.assertFalse(grade_case(case,case.expected)['release_authorized'])
        setattr(cls,'test_authored_case_%03d'%(index+1),test)
    return cls
