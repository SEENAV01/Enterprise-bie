import unittest
from app.bie.math_intelligence.missing_steps import *
class T(unittest.TestCase):
 def test_gap(self): self.assertEqual(detect_missing_steps(["a","d"],lambda a,b:3)[0].severity,"major")
 def test_none(self): self.assertEqual(detect_missing_steps(["a","b"],lambda a,b:1),())
 def test_index(self): self.assertEqual(detect_missing_steps(["a","b","z"],lambda a,b:2 if b=="z" else 1)[0].index,1)
 def test_bad(self):
  with self.assertRaises(ValueError):detect_missing_steps(["a","b"],lambda a,b:-1)
if __name__=="__main__":unittest.main()
