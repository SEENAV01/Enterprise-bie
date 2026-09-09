import unittest
from bie.misconception_intelligence.misconception_extraction import *
class T(unittest.TestCase):
 def test_common(self): self.assertEqual(extract_misconceptions("A common misconception is that force is needed for constant velocity.")[0].statement,"force is needed for constant velocity")
 def test_wrong(self): self.assertEqual(len(extract_misconceptions("It is wrong to assume that mass equals weight.")),1)
 def test_none(self): self.assertEqual(extract_misconceptions("Mass and weight differ."),[])
 def test_dedup(self):
  r=extract_misconceptions("Common misconception: mass equals weight. Common misconception: mass equals weight.")
  self.assertEqual(len(r),1)
if __name__=="__main__": unittest.main()
