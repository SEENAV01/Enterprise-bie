
import unittest
from bie.model_gateway.prompt_versioning import *
class T(unittest.TestCase):
 def p(self):return PromptTemplate("concept","v1","Teach {x}")
 def test_hash(self):self.assertEqual(len(fingerprint(self.p())),64)
 def test_registry(self):r=PromptRegistry();r.add(self.p());self.assertEqual(r.get("concept","v1").version,"v1")
 def test_duplicate(self):
  r=PromptRegistry();r.add(self.p())
  with self.assertRaises(PromptError):r.add(self.p())
 def test_missing(self):
  with self.assertRaises(PromptError):PromptRegistry().get("x","v")
 def test_empty(self):
  with self.assertRaises(PromptError):fingerprint(PromptTemplate("","v","x"))
if __name__=="__main__":unittest.main()
