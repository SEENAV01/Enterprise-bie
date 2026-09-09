
import unittest
from enterprise.dependency_scanning import *
class T(unittest.TestCase):
 def test_clear(self):self.assertTrue(gate([])["passed"])
 def test_high(self):self.assertFalse(gate([Finding("x","1","HIGH","A")])["passed"])
 def test_medium(self):self.assertTrue(gate([Finding("x","1","MEDIUM","A")])["passed"])
 def test_lock_missing(self):
  with self.assertRaises(DependencySecurityError):validate_lockfile(False,True)
 def test_lock_mutable(self):
  with self.assertRaises(DependencySecurityError):validate_lockfile(True,False)
 def test_lock_ok(self):self.assertTrue(validate_lockfile(True,True))
if __name__=="__main__":unittest.main()
