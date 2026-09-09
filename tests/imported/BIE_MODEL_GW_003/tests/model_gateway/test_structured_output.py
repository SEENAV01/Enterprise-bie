
import unittest
from bie.model_gateway.structured_output import *
class T(unittest.TestCase):
 def test_dict(self):self.assertEqual(parse_json({"a":1})["a"],1)
 def test_json(self):self.assertEqual(parse_json('{"a":1}')["a"],1)
 def test_bad(self):
  with self.assertRaises(StructuredOutputError):parse_json("x")
 def test_array(self):
  with self.assertRaises(StructuredOutputError):parse_json("[]")
 def test_fields(self):
  with self.assertRaises(StructuredOutputError):require_fields({},["a"])
 def test_ok_fields(self):self.assertEqual(require_fields({"a":1},["a"])["a"],1)
if __name__=="__main__":unittest.main()
