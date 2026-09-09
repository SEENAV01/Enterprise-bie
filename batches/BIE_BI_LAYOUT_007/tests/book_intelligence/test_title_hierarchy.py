
import unittest
from book_intelligence.title_hierarchy import *
class T(unittest.TestCase):
 def test_level1(self):self.assertEqual(infer_level({"prominence":.95}),1)
 def test_level4(self):self.assertEqual(infer_level({"prominence":.5}),4)
 def test_none(self):self.assertIsNone(infer_level({"prominence":.2}))
 def test_hierarchy(self):self.assertTrue(validate_hierarchy([{"level":1},{"level":2},{"level":2}]))
 def test_jump(self):
  with self.assertRaises(HierarchyError):validate_hierarchy([{"level":1},{"level":3}])
if __name__=="__main__":unittest.main()
