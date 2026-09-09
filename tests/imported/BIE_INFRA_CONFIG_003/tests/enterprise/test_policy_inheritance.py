
import unittest
from bie.infrastructure.policy_inheritance import *
class T(unittest.TestCase):
 def test_child_override(self): self.assertEqual(merge_policy({"locale":"en"},{"locale":"hi"})["locale"],"hi")
 def test_parent_preserved(self): self.assertEqual(merge_policy({"locale":"en"},{"deterministic":True})["locale"],"en")
 def test_nested_merge(self): self.assertEqual(merge_policy({"limits":{"a":1}},{"limits":{"b":2}})["limits"],{"a":1,"b":2})
 def test_chain(self): self.assertEqual(policy_chain({"locale":"en"},{"locale":"hi"},{"locale":"fr"})["locale"],"fr")
 def test_unknown_parent(self):
  with self.assertRaises(PolicyError): merge_policy({"x":1},{})
 def test_unknown_child(self):
  with self.assertRaises(PolicyError): merge_policy({},{"x":1})
 def test_no_mutation(self):
  p={"limits":{"a":1}}; c={"limits":{"b":2}}; merge_policy(p,c); self.assertEqual(p,{"limits":{"a":1}})
if __name__=="__main__": unittest.main()
