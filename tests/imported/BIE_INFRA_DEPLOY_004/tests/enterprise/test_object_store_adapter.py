
import unittest
from enterprise.object_store_adapter import *
class B:
 def __init__(self):self.x={}
 def put(self,k,v):self.x[k]=v
 def get(self,k):return self.x.get(k)
class T(unittest.TestCase):
 def test_roundtrip(self):
  a=ObjectStoreAdapter(B());h=a.put(b"x");self.assertEqual(a.get(h),b"x")
 def test_hash(self):self.assertEqual(len(ObjectStoreAdapter(B()).put(b"x")),64)
 def test_type(self):
  with self.assertRaises(ObjectStoreError):ObjectStoreAdapter(B()).put("x")
 def test_missing(self):
  with self.assertRaises(ObjectStoreError):ObjectStoreAdapter(B()).get("a"*64)
if __name__=="__main__":unittest.main()
