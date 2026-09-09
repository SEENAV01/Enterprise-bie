
import unittest
from bie.model_gateway.availability import *
class T(unittest.TestCase):
 def h(self,a=True,l=10):return Health("p","m",a,l,1)
 def test_usable(self):self.assertTrue(usable(self.h()))
 def test_down(self):self.assertFalse(usable(self.h(False)))
 def test_limit(self):self.assertFalse(usable(self.h(l=20),10))
 def test_choose(self):self.assertEqual(choose([self.h(l=20),Health("q","n",True,5,1)]).provider,"q")
 def test_none(self):
  with self.assertRaises(AvailabilityError):choose([self.h(False)])
if __name__=="__main__":unittest.main()
