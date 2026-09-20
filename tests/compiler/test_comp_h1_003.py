import math,unittest
from bie.compiler.vector_geometry import vector_geometry
from bie.compiler.vector_compiler import compile_vector_element
from tests.compiler.h1_test_support import element,runtime_tree,text_nodes

class VectorContractTests(unittest.TestCase):
    def p(self,v=None):return {'components':[1,2,3] if v is None else v,'projection':{'kind':'orthographic_matrix','matrix':[[1,0,0],[0,0,1]],'label':'XZ view'}}
    def test_undeclared_3d_projection_rejected(self):
        with self.assertRaisesRegex(ValueError,'VECTOR_PROJECTION_REQUIRED'):vector_geometry({'components':[1,2,3]})
    def test_zero_z_still_requires_declaration(self):
        with self.assertRaises(ValueError):vector_geometry({'components':[1,2,0]})
    def test_declared_projection_preserves_components(self):self.assertEqual(vector_geometry(self.p())['components'],[1,2,3])
    def test_declared_projection_uses_z(self):self.assertEqual(vector_geometry(self.p())['projected'],[1,3])
    def test_changing_z_changes_geometry(self):self.assertNotEqual(vector_geometry(self.p([1,2,3]))['endpoint'],vector_geometry(self.p([1,2,-3]))['endpoint'])
    def test_all_components_displayed(self):
        tree=runtime_tree(compile_vector_element(element('vector',self.p())))
        self.assertIn('(1, 2, 3)', ' '.join(text_nodes(tree)))
    def test_units_displayed(self):
        p=self.p();p['units']='m/s';self.assertEqual(vector_geometry(p)['units'],'m/s')
    def test_label_required(self):
        p=self.p();p['projection'].pop('label')
        with self.assertRaises(ValueError):vector_geometry(p)
    def test_duplicate_rows_rejected(self):
        p=self.p();p['projection']['matrix']=[[1,0,0],[1,0,0]]
        with self.assertRaisesRegex(ValueError,'VECTOR_PROJECTION_INVALID'):vector_geometry(p)
    def test_nonunit_rows_rejected(self):
        p=self.p();p['projection']['matrix']=[[2,0,0],[0,0,1]]
        with self.assertRaises(ValueError):vector_geometry(p)
    def test_nonorthogonal_rows_rejected(self):
        p=self.p();p['projection']['matrix']=[[1,0,0],[0.6,0.8,0]]
        with self.assertRaises(ValueError):vector_geometry(p)
    def test_wrong_matrix_shape_rejected(self):
        p=self.p();p['projection']['matrix']=[[1,0],[0,1]]
        with self.assertRaises(ValueError):vector_geometry(p)
    def test_view_hidden_vector_rejected(self):
        with self.assertRaisesRegex(ValueError,'VECTOR_VIEW_DEGENERATE'):vector_geometry(self.p([0,1,0]))
    def test_explicit_zero_vector_preserved(self):self.assertTrue(vector_geometry(self.p([0,0,0]))['is_zero'])
    def test_2d_zero_vector_not_divided_by_zero(self):self.assertEqual(vector_geometry({'components':[0,0]})['endpoint'],[200,145])
    def test_2d_unused_projection_rejected(self):
        with self.assertRaises(ValueError):vector_geometry(self.p([1,2]))
    def test_2d_direction_preserved(self):
        p=vector_geometry({'components':[-3,4]});self.assertLess(p['endpoint'][0],200);self.assertLess(p['endpoint'][1],145)
    def test_endpoints_remain_inside_view(self):
        for v in [[1e99,1],[1,1e99],[-1e99,-1e99]]:
            x,y=vector_geometry({'components':v})['endpoint'];self.assertTrue(100<=x<=300 and 45<=y<=245)
    def test_bool_component_rejected(self):
        with self.assertRaises(ValueError):vector_geometry({'components':[1,True]})
    def test_nonfinite_z_rejected(self):
        with self.assertRaises(ValueError):vector_geometry(self.p([1,2,math.inf]))
    def test_extra_dimension_rejected(self):
        with self.assertRaises(ValueError):vector_geometry({'components':[1,2,3,4]})
    def test_scale_is_explicit(self):self.assertGreater(vector_geometry(self.p())['scale_px_per_unit'],0)
    def test_not_accepted(self):self.assertFalse(compile_vector_element(element('vector',self.p())).accepted)

if __name__=='__main__':unittest.main()
