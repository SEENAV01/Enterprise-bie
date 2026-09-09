
import unittest
from bie.infrastructure.task_registry import *
class T(unittest.TestCase):
    def t(self,**kw):
        x=dict(task_id="BIE-X-001",title="X",system="INFRA",purpose="p")
        x.update(kw); return AtomicTask(**x)
    def test_add(self):
        r=TaskRegistry(); r.add(self.t()); self.assertEqual(r.get("BIE-X-001").title,"X")
    def test_duplicate(self):
        r=TaskRegistry(); r.add(self.t())
        with self.assertRaises(TaskRegistryError): r.add(self.t())
    def test_bad_status(self):
        with self.assertRaises(TaskRegistryError): self.t(status="DONE").validate()
    def test_self_dependency(self):
        with self.assertRaises(TaskRegistryError): self.t(dependencies=["BIE-X-001"]).validate()
    def test_duplicate_dependency(self):
        with self.assertRaises(TaskRegistryError): self.t(dependencies=["A","A"]).validate()
    def test_accepted_needs_evidence(self):
        with self.assertRaises(TaskRegistryError): self.t(status="ACCEPTED",acceptance=["x"]).validate()
    def test_accepted_valid(self):
        self.t(status="ACCEPTED",acceptance=["x"],evidence_refs=["e"]).validate()
    def test_by_system(self):
        r=TaskRegistry(); r.add(self.t()); self.assertEqual(len(r.by_system("INFRA")),1)
    def test_version(self):
        with self.assertRaises(TaskRegistryError): self.t(version=0).validate()
    def test_deterministic_export(self):
        r=TaskRegistry(); r.add(self.t()); self.assertIn("BIE-X-001",r.to_dict())
if __name__=="__main__": unittest.main()
