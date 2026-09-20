import unittest
from copy import deepcopy
from bie.compiler.diagram_compiler import *
from tests.compiler.h9_test_support import diagram_scene,runtime,nodes
from bie.compiler.generated_code_regression import probe_typescript_sources

class DiagramConsumerTests(unittest.TestCase):
    def e(self):return diagram_scene()['elements'][0]
    def bad(self,e,code):
        with self.assertRaisesRegex(ValueError,code):compile_diagram_element(e)
    def test_all_nodes_and_relations_emitted(self):
        r=compile_diagram_element(self.e());tree=runtime(r)['trees'][0]['tree'];ns=list(nodes(tree));self.assertEqual(len([n for n in ns if 'data-bie-node-id' in n.get('props',{})]),3);self.assertEqual(len([n for n in ns if 'data-bie-edge-id' in n.get('props',{})]),1)
    def test_isolated_node_preserved(self):self.assertIn('"node_id": "isolated"',compile_diagram_element(self.e()).source_text)
    def test_directed_edge_ends_on_node_boundary(self):
        e=self.e();g=diagram_geometry(e['props'],e['source_refs'],e['reasoning_refs']);self.assertEqual(g['edges'][0]['start'],[170,115]);self.assertEqual(g['edges'][0]['end'],[400,115]);self.assertTrue(g['edges'][0]['arrow'])
    def test_undirected_edge_no_arrow(self):
        e=self.e();e['props']['edges'][0]['directed']=False;g=diagram_geometry(e['props'],e['source_refs'],e['reasoning_refs']);self.assertEqual(g['edges'][0]['arrow'],[])
    def test_literal_labels_preserved(self):
        e=self.e();label='{globalThis.bad=true} <tag> اردو';e['props']['nodes'][0]['label']=label;r=compile_diagram_element(e);self.assertIn(label,str(runtime(r)))
    def test_unknown_target(self):
        e=self.e();e['props']['edges'][0]['to']='unknown';self.bad(e,'TARGET_MISSING')
    def test_duplicate_node(self):
        e=self.e();e['props']['nodes'].append(deepcopy(e['props']['nodes'][0]));self.bad(e,'DUPLICATE_NODE')
    def test_duplicate_edge(self):
        e=self.e();e['props']['edges'].append(deepcopy(e['props']['edges'][0]));self.bad(e,'DUPLICATE_EDGE')
    def test_undeclared_edge_direction(self):
        e=self.e();del e['props']['edges'][0]['directed'];self.bad(e,'FIELDS')
    def test_nonnumeric_node_position(self):
        e=self.e();e['props']['nodes'][0]['x']='20';self.bad(e,'NUMERIC')
    def test_explicit_node_geometry_required(self):
        e=self.e();del e['props']['nodes'][0]['width'];self.bad(e,'FIELDS')
    def test_outside_viewbox(self):
        e=self.e();e['props']['nodes'][0]['x']=-5;self.bad(e,'OUTSIDE')
    def test_node_overlap(self):
        e=self.e();e['props']['nodes'][1]['x']=25;self.bad(e,'NODE_OVERLAP')
    def test_edge_cannot_cross_unrelated_node(self):
        e=self.e();e['props']['nodes'][2].update(x=230,y=100,width=80,height=60);self.bad(e,'OCCLUDED')
    def test_edge_label_position_required(self):
        e=self.e();del e['props']['edges'][0]['label_position'];self.bad(e,'POSITION_REQUIRED')
    def test_edge_label_position_not_ignored(self):
        e=self.e();e['props']['edges'][0]['label']='';self.bad(e,'POSITION_REQUIRED')
    def test_node_unknown_props(self):
        e=self.e();e['props']['nodes'][0]['image']='remote';self.bad(e,'FIELDS')
    def test_self_loop_not_discarded(self):
        e=self.e();e['props']['edges'][0]['to']='a';self.bad(e,'SELF_LOOP')
    def test_edge_provenance_is_bound(self):
        e=self.e();e['props']['edges'][0]['source_refs']=['invented'];self.bad(e,'PROVENANCE')
    def test_no_inferred_semantic_fact(self):
        e=self.e();before=deepcopy(e);r=compile_diagram_element(e);self.assertEqual(e,before);self.assertFalse(r.accepted)
    def test_order_retained(self):
        e=self.e();g=diagram_geometry(e['props'],e['source_refs'],e['reasoning_refs']);self.assertEqual([n['node_id'] for n in g['nodes']],['a','b','isolated'])
    def test_real_parser(self):
        r=compile_diagram_element(self.e());self.assertEqual(probe_typescript_sources([(r.source_path,r.source_text)]).status,'PASS')

    def test_original_diagram_constructor_keeps_legacy_props_without_viewport(self):
        from bie.scene_ir.diagram_element import build
        e=diagram_scene()['elements'][0];p=e['props']
        result=build('e0',p['nodes'],p['edges'],e['source_refs'],e['reasoning_refs'],p['diagram_kind'],e['accessibility'])
        self.assertEqual(set(result.props),{'diagram_kind','nodes','edges'})
        self.assertEqual(list(result.props['nodes']),p['nodes'])
    def test_original_diagram_constructor_rejects_invalid_explicit_viewport(self):
        from bie.scene_ir.diagram_element import build
        e=diagram_scene()['elements'][0];p=e['props']
        for box in ([0,0,0,1],[0,0,float('nan'),1],[True,0,1,1],[0,0,1]):
            with self.subTest(box=box),self.assertRaises(ValueError):
                build('e0',p['nodes'],p['edges'],e['source_refs'],e['reasoning_refs'],view_box=box)
