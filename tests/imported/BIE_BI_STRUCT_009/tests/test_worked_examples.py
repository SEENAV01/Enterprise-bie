import unittest
from bie.document_intelligence.worked_examples import *
class T(unittest.TestCase):
 def test_contract(self):
  self.assertEqual(len(build("e","p",["a","b"],"x","p1")["steps"]),2)
  with self.assertRaises(E):build("e","",["a"],"x","p")
  with self.assertRaises(E):build("e","p",[],"x","p")
  with self.assertRaises(E):build("e","p",[""],"x","p")
if __name__=="__main__":unittest.main()
