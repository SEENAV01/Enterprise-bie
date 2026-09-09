import unittest
from dataclasses import replace
from bie.reasoning.decision_contracts import EvidenceRef
from bie.reasoning.geometry_reasoning import Point, polygon_measure, point_in_polygon, segment_relation, triangle_properties

class GeometryTests(unittest.TestCase):
    def setUp(self):
        self.refs=(EvidenceRef("diagram:1","primary",.95),)
        self.square=[self.p("A",0,0),self.p("B",4,0),self.p("C",4,4),self.p("D",0,4)]

    def p(self,id,x,y):return Point(id,x,y,("diagram:1",))
    def measure(self,points):return polygon_measure(points,self.refs,frame_id="f")
    def contain(self,p,points=None):return point_in_polygon(p,self.square if points is None else points,self.refs,frame_id="f").value["relation"]
    def segment(self,coords):return segment_relation(*(self.p(str(i),*p) for i,p in enumerate(coords)),self.refs,frame_id="f").value["relation"]

    def test_area_perimeter_centroid(self):
        v=self.measure(self.square).value;self.assertEqual((v["area"],v["perimeter"],v["centroid"]),(16,16,[2,2]));self.assertTrue(v["convex"])

    def test_reverse_orientation(self):
        v=self.measure(list(reversed(self.square))).value;self.assertEqual(v["area"],16);self.assertEqual(v["orientation"],"clockwise")

    def test_translation_stability(self):
        v=self.measure([replace(p,x=p.x+10**12,y=p.y-10**12) for p in self.square]).value
        self.assertEqual(v["area"],16);self.assertEqual(v["centroid"],[10**12+2,-10**12+2])

    def test_concave(self):
        points=[self.p(str(i),*p) for i,p in enumerate([(0,0),(4,0),(4,1),(1,1),(1,4),(0,4)])]
        v=self.measure(points).value;self.assertEqual(v["area"],7);self.assertFalse(v["convex"])
        self.assertEqual(self.contain(self.p("Q",2,2),points),"outside")

    def test_boundary_vertex_and_edge(self):
        self.assertEqual(self.contain(self.p("Q",0,0)),"boundary");self.assertEqual(self.contain(self.p("Q",4,2)),"boundary")

    def test_inside_outside(self):
        self.assertEqual(self.contain(self.p("Q",2,2)),"inside");self.assertEqual(self.contain(self.p("Q",5,2)),"outside")

    def test_proper_crossing(self):self.assertEqual(self.segment([(0,0),(2,2),(0,2),(2,0)]),"proper_crossing")
    def test_collinear_overlap(self):self.assertEqual(self.segment([(0,0),(4,0),(2,0),(6,0)]),"overlapping")
    def test_touching(self):self.assertEqual(self.segment([(0,0),(2,0),(2,0),(3,1)]),"touching")
    def test_disjoint(self):self.assertEqual(self.segment([(0,0),(1,0),(2,0),(3,0)]),"disjoint")

    def test_bow_tie_refused(self):
        with self.assertRaises(ValueError):self.measure([self.p(str(i),*p) for i,p in enumerate([(0,0),(3,3),(0,3),(3,0)])])

    def test_zero_area_refused(self):
        with self.assertRaises(ValueError):self.measure([self.p(str(i),i,i) for i in range(3)])

    def test_closed_duplicate_refused(self):
        with self.assertRaises(ValueError):self.measure(self.square+[self.square[0]])

    def test_nonfinite_refused(self):
        with self.assertRaises(ValueError):self.measure([replace(self.square[0],x=float("inf")),*self.square[1:]])

    def test_right_triangle(self):
        r=triangle_properties([self.p("A",0,0),self.p("B",3,0),self.p("C",0,4)],self.refs,frame_id="f")
        self.assertEqual((r.value["area"],r.value["angle_class"],r.value["side_class"]),(6,"right","scalene"))

    def test_obtuse_triangle(self):
        r=triangle_properties([self.p("A",0,0),self.p("B",4,0),self.p("C",1,1)],self.refs,frame_id="f")
        self.assertEqual(r.value["angle_class"],"obtuse")

    def test_evidence_required(self):
        with self.assertRaises(ValueError):polygon_measure(self.square,(),frame_id="f")

    def test_units_required(self):
        with self.assertRaises(ValueError):polygon_measure(self.square,self.refs,frame_id="f",unit="degrees")
