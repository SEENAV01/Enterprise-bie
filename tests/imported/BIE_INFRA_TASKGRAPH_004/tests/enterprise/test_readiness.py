
import unittest
from enterprise.readiness import *
class T(unittest.TestCase):
    def test_no_dep_ready(self):
        self.assertEqual(compute_ready({"A":{"status":"PLANNED","dependencies":[]}}),["A"])
    def test_dep_accepted_ready(self):
        t={"A":{"status":"ACCEPTED","dependencies":[]},"B":{"status":"PLANNED","dependencies":["A"]}}
        self.assertEqual(compute_ready(t),["B"])
    def test_dep_implemented_not_ready(self):
        t={"A":{"status":"IMPLEMENTED","dependencies":[]},"B":{"status":"PLANNED","dependencies":["A"]}}
        self.assertEqual(compute_ready(t),[])
    def test_missing_dep_blocks(self):
        t={"B":{"status":"PLANNED","dependencies":["A"]}}
        self.assertEqual(blockers(t,"B"),["A"])
    def test_blockers(self):
        t={"A":{"status":"PLANNED","dependencies":[]},"B":{"status":"PLANNED","dependencies":["A"]}}
        self.assertEqual(blockers(t,"B"),["A"])
    def test_unknown(self):
        with self.assertRaises(ReadinessError): blockers({},"X")
    def test_mark_ready(self):
        t={"A":{"status":"PLANNED","dependencies":[]}}
        self.assertEqual(mark_ready(t)["A"]["status"],"READY")
    def test_active_task_not_reclassified(self):
        t={"A":{"status":"IN_PROGRESS","dependencies":[]}}
        self.assertEqual(compute_ready(t),[])
if __name__=="__main__": unittest.main()
