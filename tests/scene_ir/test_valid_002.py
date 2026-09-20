import unittest
from bie.scene_ir.semantic_validation import *
class T(unittest.TestCase):
 def test_pass(self):
  d={"elements":[{"element_type":"text","props":{"text":"x"}}],"tracks":[{"action":"reveal"}]}
  self.assertTrue(validate_semantics(d).passed)
 def test_element(self):self.assertFalse(validate_semantics({"elements":[{"element_type":"magic","props":{}}]}).passed)
 def test_action(self):self.assertFalse(validate_semantics({"elements":[],"tracks":[{"action":"explode"}]}).passed)
 def test_equation(self):self.assertFalse(validate_semantics({"elements":[{"element_type":"equation","props":{}}]}).passed)
 def test_asset(self):self.assertFalse(validate_semantics({"elements":[{"element_type":"image","props":{}}]}).passed)
 def test_not_accepted(self):self.assertFalse(validate_semantics({"elements":[]}).accepted)
