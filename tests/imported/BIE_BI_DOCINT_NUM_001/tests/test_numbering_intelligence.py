import unittest
from bie.document_intelligence.numbering_intelligence import *
class T(unittest.TestCase):
 def test_contract(self):
  self.assertEqual(parse("1.2.3")["parts"],(1,2,3))
  self.assertEqual(parse("IV")["scheme"],"roman")
  self.assertEqual(parse("A")["scheme"],"alpha")
  with self.assertRaises(E):parse("section one")
if __name__=='__main__':unittest.main()
