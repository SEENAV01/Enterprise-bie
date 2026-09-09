
import unittest
from book_intelligence.list_detection import *
class T(unittest.TestCase):
 def test_ok(self):self.assertEqual(len(build_list([{"text":"a","marker_kind":"bullet","level":1}])),1)
 def test_nested(self):self.assertEqual(build_list([{"text":"a","marker_kind":"number","level":1},{"text":"b","marker_kind":"letter","level":2}])[1]["level"],2)
 def test_marker(self):
  with self.assertRaises(ListError):build_list([{"text":"a","marker_kind":"dash","level":1}])
 def test_jump(self):
  with self.assertRaises(ListError):build_list([{"text":"a","marker_kind":"number","level":1},{"text":"b","marker_kind":"letter","level":3}])
 def test_empty(self):self.assertEqual(build_list([]),())
if __name__=="__main__":unittest.main()
