import unittest
from book_intelligence.citation_normalization import *
class T(unittest.TestCase):
 def test_contract(self):
  self.assertEqual(extract("See [12].")["numeric"],(12,))
  self.assertEqual(extract("(Newton, 1687)")["author_year"],(("Newton",1687),))
  self.assertEqual(extract("none"),{"numeric":(),"author_year":()})
  with self.assertRaises(E):extract(None)
if __name__=="__main__":unittest.main()
