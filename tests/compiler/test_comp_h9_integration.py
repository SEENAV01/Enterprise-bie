import unittest,tempfile,subprocess,json
from pathlib import Path
from copy import deepcopy
from bie.compiler.shape_compiler import compile_shape_element,KINDS
from bie.compiler.diagram_compiler import compile_diagram_element
from bie.compiler.highlight_compiler import compile_highlight_element
from bie.compiler.registered_action_compiler import compile_registered_track
from bie.compiler.hardened_scene_compile import compile_h3_scene
from bie.compiler.registered_actions import ACTIONS
from tests.compiler.h9_test_support import shape_scene,diagram_scene,highlight_scene,action_scene,T,full_tree,nodes

DECLARATIONS='''// Explicit local test declarations; not the installed React/Remotion dependency tree.
declare namespace JSX {interface IntrinsicElements {[tag:string]:any;}}
declare namespace React {type ReactNode=any;type PropsWithChildren<P={}>=P & {children?:any};type FC<P={}>=(props:P)=>any; type CSSProperties=Record<string,any>;function createElement(tag:any,props:any,...children:any[]):any;}
declare module "react"{export=React;}
declare module "remotion" {export function useCurrentFrame():number;export function useVideoConfig():{fps:number;width:number;height:number};export function interpolate(v:number,x:number[],y:number[],o?:any):number;}
'''

class H9IntegrationTests(unittest.TestCase):
    def test_strict_typescript_all_new_component_families_and_empty_arrays(self):
        emitted={k:compile_shape_element(shape_scene(k)['elements'][0]) for k in KINDS}
        p=diagram_scene();emitted['diagram']=compile_diagram_element(p['elements'][0]);p['elements'][0]['props']['edges']=[];emitted['diagram_no_edges']=compile_diagram_element(p['elements'][0])
        p=diagram_scene();p['elements'][0]['props']['edges'][0]['directed']=False;emitted['diagram_undirected']=compile_diagram_element(p['elements'][0])
        for mode in ('outline','fill','spotlight','underline'):
            p=highlight_scene(mode);emitted['highlight_'+mode]=compile_highlight_element(p['elements'][-1],scene=p,target=T)
        for a in ACTIONS:
            p=action_scene(a);emitted[a]=compile_registered_track(p['tracks'][0],p['elements'][0])
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            for k,r in emitted.items():(root/(k+'.tsx')).write_text(r.source_text)
            (root/'doubles.d.ts').write_text(DECLARATIONS)
            (root/'tsconfig.json').write_text(json.dumps({'compilerOptions':{'strict':True,'noEmit':True,'target':'ES2020','module':'CommonJS','jsx':'react','esModuleInterop':True},'include':['*.tsx','*.d.ts']}))
            p=subprocess.run(['tsc','--project',str(root/'tsconfig.json')],capture_output=True,text=True,timeout=40);self.assertEqual(p.returncode,0,p.stdout+p.stderr)
    def test_crossfade_does_not_swallow_static_focus_wrapper(self):
        p=action_scene('crossfade_states');e=p['elements'][0];box=e['normalized_box'];w,h=box['width']*T.width,box['height']*T.height
        track=deepcopy(action_scene('static_focus')['tracks'][0]);track.update(track_id='outer-focus',element_id=e['element_id'],source_refs=e['source_refs'],reasoning_refs=e['reasoning_refs'],end_ms=p['duration_ms']);track['parameters'].update(viewport={'width':w,'height':h},pose={'focus_x':w/2,'focus_y':h/2,'zoom':1});p['tracks'].append(track)
        r=compile_h3_scene(p,target=T);self.assertTrue(r.receipt.source_gate_passed,r.receipt.findings);out=full_tree(r,frames=[0,23],target=T);self.assertIn('static_focus',str(out));self.assertIn('crossfade_states',str(out))
    def test_shape_and_registered_path_compose_without_dropping_shape(self):
        p=action_scene('path_endpoints_with_progress_marker');r=compile_h3_scene(p,target=T);tree=full_tree(r,frames=[5],target=T)['trees'][0]['tree'];self.assertTrue(any(n['tag']=='polyline' for n in nodes(tree)));self.assertTrue(any(n.get('props',{}).get('data-bie-progress-marker')=='stationary' for n in nodes(tree)))
    def test_diagram_source_constructor_payload_consumed_without_dsl_replacement(self):
        from bie.scene_ir.diagram_element import build
        p=diagram_scene();e=p['elements'][0];props=e['props'];created=build('e0',props['nodes'],props['edges'],e['source_refs'],e['reasoning_refs'],props['diagram_kind'],e['accessibility'],view_box=props['view_box']);self.assertEqual(created.element_type,'diagram');self.assertEqual(len(created.props['nodes']),3);emitted=compile_diagram_element(created);self.assertIn('Input {x}',emitted.source_text);self.assertEqual(emitted.source_sha256,compile_diagram_element(e).source_sha256)
    def test_shape_builder_original_kind_preserved(self):
        from bie.scene_ir.shape_element import build
        for k in KINDS:
            p=shape_scene(k);e=p['elements'][0];c=build('e0',k,e['source_refs'],e['reasoning_refs'],e['props']['geometry'],e['props']['style'],e['accessibility']);self.assertEqual(compile_shape_element(c).element_type,'shape')
    def test_no_new_external_runtime_dependencies(self):
        r=compile_h3_scene(diagram_scene(),target=T);package=json.loads(next(f.content for f in r.codegen.files if f.path=='package.json'));self.assertNotIn('d3',package['dependencies']);self.assertNotIn('cytoscape',package['dependencies'])
    def test_fail_closed_unknown_shape_parameter(self):
        p=shape_scene();p['elements'][0]['props']['world_geometry']=True;r=compile_h3_scene(p,target=T);self.assertFalse(r.receipt.source_gate_passed)
    def test_all_declared_actions_pass_checked_publication_gate(self):
        self.assertEqual(len(ACTIONS),7);self.assertTrue(all(compile_h3_scene(action_scene(a),target=T).receipt.source_gate_passed for a in ACTIONS))
