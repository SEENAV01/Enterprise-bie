import unittest
from book_intelligence.orientation_handling import *
class T(unittest.TestCase):
 def test_contract(self):
  self.assertEqual(normalize(90,600,800)["logical_width"],800)
  self.assertEqual(normalize(0,600,800)["logical_width"],600)
  self.assertEqual(normalize(270,600,800)["logical_height"],600)
  with self.assertRaises(E):normalize(45,1,1)
if __name__=='__main__':unittest.main()
