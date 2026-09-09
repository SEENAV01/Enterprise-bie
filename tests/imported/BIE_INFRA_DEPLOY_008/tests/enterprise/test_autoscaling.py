
import unittest
from enterprise.autoscaling import *
class T(unittest.TestCase):
 def p(self):return ScalePolicy(1,10,2,30)
 def test_min(self):self.assertEqual(desired(self.p(),0,5),1)
 def test_scale(self):self.assertEqual(desired(self.p(),5,1),3)
 def test_max(self):self.assertEqual(desired(self.p(),100,1),10)
 def test_bad(self):
  with self.assertRaises(AutoscaleError):desired(ScalePolicy(2,1,1,1),1,1)
 def test_target(self):
  with self.assertRaises(AutoscaleError):desired(ScalePolicy(1,2,0,1),1,1)
if __name__=="__main__":unittest.main()
