import math,unittest
from bie.compiler.model2d_geometry import model2d_geometry
from bie.compiler.model2d_compiler import compile_model2d_element
from tests.compiler.h1_test_support import element,runtime_tree,nodes

class TopologyTests(unittest.TestCase):
    def p(self,edges=None):return {'vertices':[[0,0],[1,0],[1,1]],'edges':[[0,1],[1,2]] if edges is None else edges}
    def test_valid_topology_preserved(self):self.assertEqual(model2d_geometry(self.p())['edges'],[[0,1],[1,2]])
    def test_out_of_range_index_rejected(self):
        with self.assertRaisesRegex(ValueError,'MODEL2D_EDGE_INDEX_INVALID'):model2d_geometry(self.p([[0,5]]))
    def test_negative_index_rejected(self):
        with self.assertRaises(ValueError):model2d_geometry(self.p([[-1,1]]))
    def test_float_index_rejected(self):
        with self.assertRaises(ValueError):model2d_geometry(self.p([[0,1.0]]))
    def test_bool_index_rejected(self):
        with self.assertRaises(ValueError):model2d_geometry(self.p([[False,1]]))
    def test_string_index_rejected(self):
        with self.assertRaises(ValueError):model2d_geometry(self.p([['0',1]]))
    def test_one_entry_edge_rejected(self):
        with self.assertRaises(ValueError):model2d_geometry(self.p([[0]]))
    def test_extra_entry_edge_rejected(self):
        with self.assertRaises(ValueError):model2d_geometry(self.p([[0,1,2]]))
    def test_nonsequence_edge_rejected(self):
        with self.assertRaises(ValueError):model2d_geometry(self.p([3]))
    def test_duplicate_edge_rejected(self):
        with self.assertRaisesRegex(ValueError,'MODEL2D_DUPLICATE_EDGE'):model2d_geometry(self.p([[0,1],[0,1]]))
    def test_reversed_duplicate_edge_rejected(self):
        with self.assertRaises(ValueError):model2d_geometry(self.p([[0,1],[1,0]]))
    def test_self_loop_rejected(self):
        with self.assertRaisesRegex(ValueError,'MODEL2D_SELF_LOOP'):model2d_geometry(self.p([[0,0]]))
    def test_duplicate_vertex_rejected(self):
        p=self.p();p['vertices'][2]=[0,0]
        with self.assertRaises(ValueError):model2d_geometry(p)
    def test_nonfinite_coordinate_rejected(self):
        p=self.p();p['vertices'][0][0]=math.nan
        with self.assertRaises(ValueError):model2d_geometry(p)
    def test_unconverted_coordinate_rejected(self):
        p=self.p();p['vertices'][0]=[20,30]
        with self.assertRaises(ValueError):model2d_geometry(p)
    def test_undeclared_coordinate_space_rejected(self):
        p=self.p();p['coordinate_space']='meters'
        with self.assertRaises(ValueError):model2d_geometry(p)
    def test_vertex_extra_dimension_rejected(self):
        p=self.p();p['vertices'][0]=[0,0,0]
        with self.assertRaises(ValueError):model2d_geometry(p)
    def test_empty_edges_still_emit_vertices(self):
        tree=runtime_tree(compile_model2d_element(element('model2d',self.p([]))));self.assertEqual(len(nodes(tree,'circle')),3);self.assertFalse(nodes(tree,'line'))
    def test_actual_tsx_edges_reference_valid_endpoints(self):
        tree=runtime_tree(compile_model2d_element(element('model2d',self.p())));lines=nodes(tree,'line');self.assertEqual(lines[0]['props']['x1'],8);self.assertEqual(lines[0]['props']['x2'],392)
    def test_empty_vertices_rejected(self):
        p=self.p();p['vertices']=[]
        with self.assertRaises(ValueError):model2d_geometry(p)
    def test_edges_budget_rejected(self):
        with self.assertRaises(ValueError):model2d_geometry(self.p([[0,1]]*4001))
    def test_bad_geometry_never_returns_source(self):
        with self.assertRaises(ValueError):compile_model2d_element(element('model2d',self.p([[0,5]])))
    def test_not_accepted(self):self.assertFalse(compile_model2d_element(element('model2d',self.p())).accepted)

if __name__=='__main__':unittest.main()
