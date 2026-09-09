
import unittest
from bie.model_gateway.fallback_router import *
class R(Exception):pass
class F(Exception):pass
class T(unittest.TestCase):
 def test_first(self):self.assertEqual(execute(["a"],lambda c:"ok",lambda e:True)[0],"a")
 def test_fallback(self):
  def f(c):
   if c=="a":raise R()
   return "ok"
  self.assertEqual(execute(["a","b"],f,lambda e:isinstance(e,R))[0],"b")
 def test_fatal(self):
  with self.assertRaises(F):execute(["a","b"],lambda c:(_ for _ in ()).throw(F()),lambda e:False)
 def test_all(self):
  with self.assertRaises(FallbackError):execute(["a"],lambda c:(_ for _ in ()).throw(R()),lambda e:True)
if __name__=="__main__":unittest.main()
