import unittest
from bie.reasoning.evidence_conflict import *
class T(unittest.TestCase):
 def test_conflict(self): self.assertEqual(len(conflicts([Position("a","p",1,.9),Position("b","p",-1,.8)])),1)
 def test_none(self): self.assertEqual(conflicts([Position("a","p",1,.9),Position("b","p",1,.8)]),())
 def test_severity(self): self.assertEqual(conflicts([Position("a","p",1,.9),Position("b","p",-1,.6)])[0].severity,.6)
 def test_bad(self):
  with self.assertRaises(ValueError):conflicts([Position("a","p",0,.5)])
if __name__=="__main__":unittest.main()
