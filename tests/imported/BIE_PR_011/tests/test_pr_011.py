import unittest
from bie.prerequisite_intelligence.foundational import *
class T(unittest.TestCase):
 def test_root_hub(self):
  r=identify_foundational({"a","b","c"},[("a","b"),("a","c")]); self.assertEqual(r[0].id,"a")
 def test_salience(self): self.assertGreater(identify_foundational({"a"},[],{"a":1})[0].score,.5)
 def test_unknown(self):
  with self.assertRaises(ValueError): identify_foundational({"a"},[("a","b")])
 def test_deterministic(self): self.assertEqual(identify_foundational({"b","a"},[])[0].id,"a")
if __name__=="__main__": unittest.main()
