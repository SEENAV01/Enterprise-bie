import unittest
from bie.document_intelligence.coordinate_provenance import *
class T(unittest.TestCase):
 def test_contract(self):
  self.assertEqual(to_pixels((0,0,.5,.5),100,200),(0,0,50,100))
  with self.assertRaises(E):to_pixels((0,0,1,1),0,1)
  with self.assertRaises(E):to_pixels((0,0,2,1),100,100)
  with self.assertRaises(E):to_pixels((0,0,1),100,100)
if __name__=="__main__":unittest.main()
