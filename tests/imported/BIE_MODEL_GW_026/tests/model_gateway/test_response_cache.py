
import unittest
from bie.model_gateway.response_cache import *
class T(unittest.TestCase):
 def test_hit(self):c=ResponseCache();c.put("k","v",10);self.assertEqual(c.get("k",1),"v")
 def test_miss(self):self.assertIsNone(ResponseCache().get("k",1))
 def test_expire(self):c=ResponseCache();c.put("k","v",1);self.assertIsNone(c.get("k",1))
 def test_empty(self):
  with self.assertRaises(CacheError):ResponseCache().put("","v",1)
if __name__=="__main__":unittest.main()
