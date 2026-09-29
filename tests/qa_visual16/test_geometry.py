import unittest
from fractions import Fraction
from bie.qa.visual_v2 import Rect,RGBA
from bie.qa.visual_v2.geometry import *


class GeometryTests(unittest.TestCase):
    def test_touching_is_not_collision(self):self.assertIsNone(intersection(Rect(0,0,10,10),Rect(10,0,10,10)))
    def test_one_millipixel_collision_is_not_rounded_away(self):self.assertEqual(intersection(Rect(0,0,10,10),Rect(9,9,10,10)).area,1)
    def test_union_not_sum(self):self.assertEqual(union_area((Rect(0,0,10,10),Rect(5,0,10,10))),150)
    def test_duplicate_area_no_credit(self):self.assertEqual(union_area((Rect(0,0,10,10),)*10),100)
    def test_negative_position_clipped(self):self.assertEqual(area_ppm((Rect(-5,-5,10,10),),Rect(0,0,10,10)),250000)
    def test_contains_edge_tolerance(self):
        a=Rect(0,0,100,100);b=Rect(-1,0,101,100)
        self.assertFalse(contains(a,b));self.assertTrue(contains(a,b,1))
    def test_gap_squared(self):self.assertEqual(gap_squared(Rect(0,0,10,10),Rect(13,14,10,10)),25)
    def test_local_grid_peak(self):self.assertEqual(grid_peak((Rect(0,0,10,10),Rect(3,3,10,10)),Rect(0,0,100,100),2,2),2)
    def test_exact_fraction_area(self):self.assertEqual(area_ppm((Rect(0,0,1,1),),Rect(0,0,3,3)),Fraction(1000000,9))
    def test_union_matches_integer_raster_oracle(self):
        import random
        rand=random.Random(803)
        for _ in range(250):
            rs=tuple(Rect(rand.randrange(-4,5),rand.randrange(-4,5),rand.randrange(1,6),rand.randrange(1,6)) for j in range(rand.randrange(1,9)))
            pixels={(x,y) for r in rs for x in range(r.x,r.right) for y in range(r.y,r.bottom)}
            with self.subTest(rectangles=rs):self.assertEqual(union_area(rs),len(pixels))
    def test_symmetry_and_monotonicity(self):
        for x in range(-10,11):
            for y in range(-3,4):
                a=Rect(0,0,10,10);b=Rect(x,y,4,5)
                with self.subTest(x=x,y=y):
                    self.assertEqual(intersection(a,b),intersection(b,a));self.assertGreaterEqual(union_area((a,b)),a.area)
    def test_black_white_contrast(self):self.assertAlmostEqual(contrast_ratio(RGBA(0,0,0),RGBA(255,255,255),1000000),21)
    def test_same_color_contrast(self):self.assertEqual(contrast_ratio(RGBA(33,77,128),RGBA(33,77,128),1000000),1)
    def test_alpha_compositing(self):self.assertLess(contrast_ratio(RGBA(0,0,0,100),RGBA(255,255,255),1000000),4.5)
    def test_group_opacity_reduces_contrast(self):self.assertLess(contrast_ratio(RGBA(0,0,0),RGBA(255,255,255),500000),4.5)
    def test_contrast_not_rounded_up(self):
        self.assertLess(contrast_ratio(RGBA(119,119,119),RGBA(255,255,255),1000000),4.5)
        self.assertGreater(contrast_ratio(RGBA(118,118,118),RGBA(255,255,255),1000000),4.5)
    def test_grayscale_contrast_monotone(self):
        values=[contrast_ratio(RGBA(c,c,c),RGBA(255,255,255),1000000) for c in range(256)]
        for a,b in zip(values,values[1:]):
            with self.subTest(previous=a,next=b):self.assertGreater(a,b)
