
import unittest
from bie.infrastructure.side_effect_guard import *
class C:
 def __init__(self): self.x={}
 def claim(self,k,f,o):
  if k not in self.x: self.x[k]=type("R",(),{"state":"CLAIMED","owner":o,"result_ref":None,"fingerprint":f})()
  elif self.x[k].fingerprint!=f: raise RuntimeError("conflict")
  return self.x[k]
 def complete(self,k,o,r):
  x=self.x[k]
  if x.owner!=o: raise RuntimeError("owner")
  x.state="COMPLETED";x.result_ref=r;return x
class T(unittest.TestCase):
 def test_fp_deterministic(self): self.assertEqual(fingerprint("x",{"a":1,"b":2}),fingerprint("x",{"b":2,"a":1}))
 def test_begin_execute(self): self.assertTrue(SideEffectGuard(C()).begin("k","render",{"x":1},"w")["execute"])
 def test_completed_skips(self):
  c=C();g=SideEffectGuard(c);g.begin("k","render",{},"w");g.commit("k","w","a");self.assertFalse(g.begin("k","render",{},"w")["execute"])
 def test_result_returned(self):
  c=C();g=SideEffectGuard(c);g.begin("k","render",{},"w");g.commit("k","w","a");self.assertEqual(g.begin("k","render",{},"w")["result_ref"],"a")
 def test_foreign_active(self):
  c=C();g=SideEffectGuard(c);g.begin("k","render",{},"w")
  with self.assertRaises(SideEffectError): g.begin("k","render",{},"x")
 def test_operation_required(self):
  with self.assertRaises(SideEffectError): fingerprint("",{})
if __name__=="__main__": unittest.main()
