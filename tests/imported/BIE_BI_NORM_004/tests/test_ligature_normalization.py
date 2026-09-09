import unittest
from bie.document_intelligence.ligature_normalization import *
class T(unittest.TestCase):
 def test_contract(self):
  self.assertEqual(normalize("ﬁeld"),"field")
  self.assertEqual(normalize("oﬃce"),"office")
  self.assertEqual(normalize("abc"),"abc")
  with self.assertRaises(E):normalize(None)
if __name__=="__main__":unittest.main()
