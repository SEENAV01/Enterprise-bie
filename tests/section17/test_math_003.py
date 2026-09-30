import math
from domain_helpers import DomainBase,q,vec
from bie.evaluation.benchmarks.domains.geometry import solve

class GeometryTests(DomainBase):
    def polygon(self,vertices):return dict(op='simple_polygon_area',vertices=vertices,unit='m')
    def test_authored_reference_pack(self):self.replay_pack('BIE-EVAL-MATH-003')
    def test_heron_independent_right_triangle(self):self.assertEqual({'area_m2':30,'perimeter_m':30},solve(dict(op='triangle_sides',sides=[q(5,'m'),q(12,'m'),q(13,'m')])) )
    def test_triangle_permutation(self):
        a=solve(dict(op='triangle_sides',sides=[q(5,'m'),q(12,'m'),q(13,'m')]));b=solve(dict(op='triangle_sides',sides=[q(13,'m'),q(5,'m'),q(12,'m')]));self.assertEqual(a,b)
    def test_equilateral_triangle(self):self.assertAlmostEqual(math.sqrt(3),solve(dict(op='triangle_sides',sides=[q(2,'m')]*3))['area_m2'])
    def test_triangle_inequality_rejected(self):self.code('DEGENERATE_OR_IMPOSSIBLE_TRIANGLE',solve,dict(op='triangle_sides',sides=[q(1,'m'),q(2,'m'),q(4,'m')]))
    def test_negative_side_rejected(self):self.code('NONPOSITIVE_QUANTITY',solve,dict(op='triangle_sides',sides=[q(-3,'m'),q(4,'m'),q(5,'m')]))
    def test_polygon_translation_invariance(self):
        p=[[0,0],[3,0],[3,2],[0,2]];a=solve(self.polygon(p));b=solve(self.polygon([[x+7,y-12] for x,y in p]));self.assertEqual(a,b)
    def test_polygon_orientation_does_not_negate_area(self):
        p=[[0,0],[3,0],[3,2],[0,2]];a=solve(self.polygon(p));b=solve(self.polygon(p[::-1]));self.assertEqual(a['area_m2'],b['area_m2']);self.assertNotEqual(a['orientation'],b['orientation'])
    def test_polygon_unit_area_conversion(self):
        d=self.polygon([[0,0],[300,0],[300,200],[0,200]]);d['unit']='cm';self.assertEqual(6,solve(d)['area_m2'])
    def test_collinear_forward_boundary_vertex_allowed(self):self.assertEqual(2,solve(self.polygon([[0,0],[1,0],[2,0],[2,1],[0,1]]))['area_m2'])
    def test_collinear_backtrack_rejected(self):self.code('POLYGON_EDGE_BACKTRACK',solve,self.polygon([[0,0],[2,0],[1,0],[1,1],[0,1]]))
    def test_self_intersection_rejected(self):self.code('NON_SIMPLE_POLYGON',solve,self.polygon([[0,0],[2,2],[0,2],[2,0]]))
    def test_repeated_vertex_rejected(self):self.code('REPEATED_POLYGON_VERTEX',solve,self.polygon([[0,0],[1,0],[0,0],[0,1]]))
    def test_rigid_transform_preserves_distance(self):
        r=solve(dict(op='rigid_transform_2d',points=[[0,0],[3,4]],unit='m',angle=q(71,'deg'),translation=vec((11,-8),'m')))['points_m'];self.assertAlmostEqual(5,math.dist(*r))
    def test_full_rotation_identity(self):
        r=solve(dict(op='rigid_transform_2d',points=[[2,5]],unit='m',angle=q(360,'deg'),translation=vec((0,0),'m')))['points_m'][0];self.assertAlmostEqual(2,r[0]);self.assertAlmostEqual(5,r[1])
    def test_similarity_square_law(self):self.assertEqual(100,solve(dict(op='similar_figure_area',base_area=q(4,'m^2'),length_scale=5))['area_m2'])
    def test_zero_scale_rejected(self):self.code('NONPOSITIVE_SCALE',solve,dict(op='similar_figure_area',base_area=q(4,'m^2'),length_scale=0))
    def test_invalid_coordinate_dimension_rejected(self):self.code('VECTOR_DIMENSION_MISMATCH',solve,self.polygon([[0,0,0],[1,0,0],[0,1,0]]))
    def test_wrong_similarity_linear_seed_rejected(self):self.mutant('BIE-EVAL-MATH-003',8,['values','area_m2'],12)
    def test_wrong_orientation_seed_rejected(self):self.mutant('BIE-EVAL-MATH-003',3,['values','orientation'],'CW')
