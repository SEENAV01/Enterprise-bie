
import unittest
from dataclasses import dataclass
from enterprise.rollback_rules import *
@dataclass
class M: version:int; down_sql:str|None
class T(unittest.TestCase):
 def test_plan(self): self.assertEqual([m.version for m in rollback_plan([M(1,"a"),M(2,"b")],2,0)],[2,1])
 def test_partial(self): self.assertEqual([m.version for m in rollback_plan([M(1,"a"),M(2,"b")],2,1)],[2])
 def test_irreversible(self):
  with self.assertRaises(RollbackError): rollback_plan([M(1,None)],1,0)
 def test_bad_target(self):
  with self.assertRaises(RollbackError): rollback_plan([],1,2)
 def test_prod_guard(self):
  with self.assertRaises(RollbackError): assert_rollback_allowed("production",False,"")
 def test_prod_allowed(self): self.assertTrue(assert_rollback_allowed("production",True,"backup"))
 def test_dev(self): self.assertTrue(assert_rollback_allowed("dev",False,""))
if __name__=="__main__": unittest.main()
