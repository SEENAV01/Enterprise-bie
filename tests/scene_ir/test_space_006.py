import unittest
from bie.scene_ir.z_order import *
class T(unittest.TestCase):
 def test_sort(self):self.assertEqual([x.element_id for x in resolve_z_order([ZOrderEntry("a",1,"content"),ZOrderEntry("b",0,"background")])],["b","a"])
 def test_layer_order(self):self.assertEqual(resolve_z_order([ZOrderEntry("u",0,"ui"),ZOrderEntry("o",99,"overlay")])[0].element_id,"o")
 def test_dup(self):
  with self.assertRaises(SpaceIRError):resolve_z_order([ZOrderEntry("a",1),ZOrderEntry("a",2)])
 def test_layer(self):
  with self.assertRaises(SpaceIRError):ZOrderEntry("a",1,"weird")
 def test_int(self):
  with self.assertRaises(SpaceIRError):ZOrderEntry("a",1.5)
