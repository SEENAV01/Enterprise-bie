
import unittest
from bie.model_gateway.schema_validation import *
class T(unittest.TestCase):
 def test_obj(self):self.assertTrue(validate({"a":"x"},{"type":"object","required":["a"],"properties":{"a":{"type":"string"}}}))
 def test_missing(self):
  with self.assertRaises(SchemaValidationError):validate({},{"type":"object","required":["a"]})
 def test_type(self):
  with self.assertRaises(SchemaValidationError):validate({"a":1},{"type":"object","properties":{"a":{"type":"string"}}})
 def test_array(self):self.assertTrue(validate([1,2],{"type":"array","items":{"type":"number"}}))
 def test_enum(self):
  with self.assertRaises(SchemaValidationError):validate("x",{"type":"string","enum":["a"]})
 def test_bool_not_num(self):
  with self.assertRaises(SchemaValidationError):validate(True,{"type":"number"})
if __name__=="__main__":unittest.main()
