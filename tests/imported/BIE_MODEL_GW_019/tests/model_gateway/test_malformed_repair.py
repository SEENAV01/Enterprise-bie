
import unittest
from model_gateway.malformed_repair import *
class T(unittest.TestCase):
 def test_plain(self):self.assertEqual(repair_json('{"a":1}')["a"],1)
 def test_fence(self):self.assertEqual(repair_json('```json\n{"a":1}\n```')["a"],1)
 def test_wrapper(self):self.assertEqual(repair_json('answer: {"a":1} done')["a"],1)
 def test_bad(self):
  with self.assertRaises(RepairError):repair_json("no json")
 def test_type(self):
  with self.assertRaises(RepairError):repair_json(1)
if __name__=="__main__":unittest.main()
