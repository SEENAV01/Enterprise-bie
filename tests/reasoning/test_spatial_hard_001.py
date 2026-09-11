import unittest
from bie.reasoning.spatial_frame_units import SpatialFrame,SpatialPoint,FrameTransform,assert_compatible,transform_point

class TestSpatialFrameUnits(unittest.TestCase):
    def test_same_frame_is_compatible(self):
        f=SpatialFrame("local",2,"m",("x","y"))
        assert_compatible(SpatialPoint(f,(1,2)),SpatialPoint(f,(3,4)))

    def test_unit_mismatch_rejected(self):
        a=SpatialPoint(SpatialFrame("f",2,"m",("x","y")),(1,2))
        b=SpatialPoint(SpatialFrame("f",2,"ft",("x","y")),(1,2))
        with self.assertRaises(ValueError):
            assert_compatible(a,b)

    def test_explicit_transform_preserves_provenance(self):
        a=SpatialPoint(SpatialFrame("a",2,"m",("x","y")),(1,2),("src",))
        tf=FrameTransform("a","b","tx1",("calibration",))
        b=transform_point(a,SpatialFrame("b",2,"m",("x","y")),tf,lambda c:(c[0]+1,c[1]+1))
        self.assertIn("tx1",b.provenance_ids)
        self.assertIn("calibration",b.provenance_ids)
