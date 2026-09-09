import unittest
from bie.evaluation.contracts import *

def metric(mid="source_grounding", critical=True, minimum=.9):
    return MetricSpec(mid,1.0,minimum,critical,1)

def case(cid="c1",domain="physics",metrics=None,threshold=.9):
    return BenchmarkCase(cid,"Case",domain,"1.0.0","fixture",["x"],metrics or [metric()],threshold)

def evidence(mid="source_grounding",score=1.0,eid="ev"):
    return MetricEvidence(mid,score,"tester","1.0.0",[eid])

class EvaluationTests(unittest.TestCase):
    def test_case_pass(self):
        c=case()
        r=BenchmarkEvaluator.evaluate_case(c,[evidence()])
        self.assertEqual(r.status,"PASS")

    def test_missing_critical_evidence_fails(self):
        c=case()
        r=BenchmarkEvaluator.evaluate_case(c,[])
        self.assertEqual(r.status,"FAIL")
        self.assertIn("source_grounding",r.missing_evidence_metrics)

    def test_critical_floor_cannot_be_hidden_by_average(self):
        c=case(metrics=[metric("source_grounding",True,.95),MetricSpec("style",10,.2,False,1)],threshold=.5)
        r=BenchmarkEvaluator.evaluate_case(c,[evidence("source_grounding",.94),evidence("style",1.0,"e2")])
        self.assertEqual(r.status,"FAIL")
        self.assertIn("source_grounding",r.failed_metrics)

    def test_conservative_multiple_evidence(self):
        c=case()
        r=BenchmarkEvaluator.evaluate_case(c,[evidence(score=.98),evidence(score=.88,eid="e2")])
        self.assertEqual(r.metric_scores["source_grounding"],.88)

    def test_suite_requires_all_required_cases(self):
        c1=case("p","physics")
        c2=case("m","mathematics")
        suite=BenchmarkSuite("s","1.0.0",[c1,c2],
            [DomainRequirement("physics",.9),DomainRequirement("mathematics",.9)],.9)
        r1=BenchmarkEvaluator.evaluate_case(c1,[evidence()])
        sr=BenchmarkEvaluator.evaluate_suite(suite,[r1])
        self.assertEqual(sr.status,"FAIL")
        self.assertIn("m",sr.failed_cases)

    def test_domain_floor(self):
        c=case("p","physics",threshold=.7)
        suite=BenchmarkSuite("s","1.0.0",[c],[DomainRequirement("physics",.95)],.7)
        r=CaseResult("p","PASS",.9,{},[],[])
        sr=BenchmarkEvaluator.evaluate_suite(suite,[r])
        self.assertEqual(sr.status,"FAIL")
        self.assertIn("physics",sr.domain_failures)

    def test_suite_pass(self):
        cs=[case("p","physics"),case("m","mathematics")]
        suite=BenchmarkSuite("s","1.0.0",cs,
            [DomainRequirement("physics",.9),DomainRequirement("mathematics",.9)],.9)
        rs=[BenchmarkEvaluator.evaluate_case(c,[evidence()]) for c in cs]
        sr=BenchmarkEvaluator.evaluate_suite(suite,rs)
        self.assertEqual(sr.status,"PASS")

    def test_duplicate_case_rejected(self):
        c=case()
        suite=BenchmarkSuite("s","1.0.0",[c,c],[DomainRequirement("physics",.9)],.9)
        with self.assertRaises(EvaluationContractError):suite.validate()

    def test_requirement_needs_case(self):
        c=case()
        suite=BenchmarkSuite("s","1.0.0",[c],[DomainRequirement("biology",.9)],.9)
        with self.assertRaises(EvaluationContractError):suite.validate()

if __name__=="__main__":unittest.main()
