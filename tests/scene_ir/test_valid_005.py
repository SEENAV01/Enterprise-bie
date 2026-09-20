import unittest
from bie.scene_ir.spatial_validation import *
class T(unittest.TestCase):
 def test_pass(self):self.assertTrue(validate_spatial({"layout":{"boxes":[{"x":0,"y":0,"width":.5,"height":.5}]}}).passed)
 def test_box(self):self.assertFalse(validate_spatial({"layout":{"boxes":[{"x":.8,"y":0,"width":.5,"height":.5}]}}).passed)
 def test_type(self):self.assertFalse(validate_spatial({"layout":{"boxes":[{"x":"a","y":0,"width":.5,"height":.5}]}}).passed)
 def test_contradiction(self):
  d={"layout":{"relative_constraints":[{"subject_id":"a","relation":"left_of","reference_id":"b"},{"subject_id":"a","relation":"right_of","reference_id":"b"}]}}
  self.assertFalse(validate_spatial(d).passed)
 def test_empty(self):self.assertTrue(validate_spatial({}).passed)
 def test_not_accepted(self):self.assertFalse(validate_spatial({}).accepted)
