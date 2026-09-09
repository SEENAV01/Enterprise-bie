
import unittest
from bie.model_gateway.semantic_cache import *
class T(unittest.TestCase):
 def test_cos(self):self.assertAlmostEqual(cosine([1,0],[1,0]),1)
 def test_match(self):self.assertEqual(best_match([1,0],[{"id":"a","vector":[1,0]}],.9)[1]["id"],"a")
 def test_none(self):self.assertIsNone(best_match([1,0],[{"id":"a","vector":[0,1]}],.9))
 def test_dim(self):
  with self.assertRaises(SemanticCacheError):cosine([1],[1,2])
 def test_zero(self):self.assertEqual(cosine([0,0],[1,0]),0)
if __name__=="__main__":unittest.main()
