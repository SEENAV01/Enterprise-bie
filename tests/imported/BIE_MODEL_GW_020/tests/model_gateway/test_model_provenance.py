
import unittest
from model_gateway.model_provenance import *
class T(unittest.TestCase):
 def test_hash(self):self.assertEqual(len(request_hash({"a":1})),64)
 def test_stable(self):self.assertEqual(request_hash({"b":2,"a":1}),request_hash({"a":1,"b":2}))
 def test_valid(self):self.assertTrue(validate(ModelProvenance("p","m","a"*64,"v1",1,2)))
 def test_hash_bad(self):
  with self.assertRaises(ProvenanceError):validate(ModelProvenance("p","m","x","v",1,2))
 def test_time(self):
  with self.assertRaises(ProvenanceError):validate(ModelProvenance("p","m","a"*64,"v",2,1))
if __name__=="__main__":unittest.main()
