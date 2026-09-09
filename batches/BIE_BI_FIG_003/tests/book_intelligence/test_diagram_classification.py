
import unittest
from book_intelligence.diagram_classification import *
class T(unittest.TestCase):
 def test_map(self):self.assertEqual(classify({"map":.9})[0],"map")
 def test_unknown(self):self.assertEqual(classify({"map":.2})[0],"unknown")
 def test_empty(self):self.assertEqual(classify({})[0],"unknown")
 def test_bad(self):
  with self.assertRaises(DiagramClassError):classify({"alien":.9})
 def test_range(self):
  with self.assertRaises(DiagramClassError):classify({"map":2})
if __name__=="__main__":unittest.main()
