
import unittest
from bie.model_gateway.embeddings_contract import *
class T(unittest.TestCase):
 def test_ok(self):self.assertTrue(validate(EmbeddingResult("m",((1.,2.),),2),1))
 def test_count(self):
  with self.assertRaises(EmbeddingError):validate(EmbeddingResult("m",(),2),1)
 def test_dim(self):
  with self.assertRaises(EmbeddingError):validate(EmbeddingResult("m",((1.,),),2),1)
 def test_zero(self):
  with self.assertRaises(EmbeddingError):validate(EmbeddingResult("m",((),),0),1)
if __name__=="__main__":unittest.main()
