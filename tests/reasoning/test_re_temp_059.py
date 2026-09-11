import unittest
from bie.reasoning.temporal_integration_bundle_validator import *

class T(unittest.TestCase):
    def task(self,n,ok=True):
        return BundleTask(f"BIE-RE-TEMP-{n:03d}",ok,ok,ok,ok,ok)
    def test_ready_small_range(self):
        r=validate_bundle([self.task(4),self.task(5)],4,5)
        self.assertEqual(r["state"],"READY")
    def test_missing(self):
        r=validate_bundle([self.task(4)],4,5)
        self.assertEqual(r["missing"],("BIE-RE-TEMP-005",))
    def test_invalid(self):
        r=validate_bundle([self.task(4,False)],4,4)
        self.assertEqual(r["invalid"],("BIE-RE-TEMP-004",))
    def test_extra_nonblocking(self):
        r=validate_bundle([self.task(4),self.task(6)],4,4)
        self.assertEqual(r["state"],"READY")
        self.assertEqual(r["extra"],("BIE-RE-TEMP-006",))
