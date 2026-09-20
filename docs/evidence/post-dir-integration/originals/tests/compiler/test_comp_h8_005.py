import unittest,subprocess,tempfile,json,shutil,inspect
from pathlib import Path
from bie.compiler.real_paint import capture_entry_h8,produce_actual_paint,require_actual_witness
from bie.compiler.raster_capture import build_raster_targets,DIAGNOSTIC_SCOPE
from bie.compiler.hardened_scene_compile import publish_h3_scene
from tests.compiler.h8_test_support import raw_text,BROWSER
ROOT=Path(__file__).parents[2]
SUPPORT=ROOT/'app/bie/compiler/qa_support'

def req():return {'nonce':'diagnostic-test-not-execution','composition_id':'Test','width':640,'height':360,'fps':4,'frame_count':2,'equationFonts':{},'rasterTargets':build_raster_targets(raw_text())}

class ActualProducerAdoptionTests(unittest.TestCase):
    def test_original_scene_not_replaced(self):s=capture_entry_h8(req(),'x=>[]','x=>[]');self.assertIn('<><Scene/><Observer/></>',s);self.assertIn('"./src/Scene"',s)
    def test_frame_and_mode_bound_hooks(self):s=capture_entry_h8(req(),'x=>[]','x=>[]');self.assertIn('[frame,modeKey]',s);self.assertIn('[frame,handle,modeKey]',s)
    def test_remotion_inputprops_used(self):s=capture_entry_h8(req(),'x=>[]','x=>[]');self.assertIn('getInputProps()',s);self.assertIn('__bieRasterMode',s)
    def test_fonts_before_raster_measurement(self):s=capture_entry_h8(req(),'x=>[]','x=>[]');self.assertLess(s.index('await document.fonts.ready'),s.index('const raster ='));self.assertIn('raster,fonts_ready',s)
    def test_actual_controller_node_syntax(self):p=subprocess.run(['node','--check',str(SUPPORT/'remotion_raster_capture.cjs')],capture_output=True,text=True);self.assertEqual(p.returncode,0,p.stderr)
    def test_actual_controller_has_no_diagnostic_bridge(self):s=(SUPPORT/'remotion_raster_capture.cjs').read_text();self.assertIn('@remotion/renderer',s);self.assertNotIn('layout_bridge',s);self.assertNotIn('frame_runtime_bridge',s);self.assertIn('renderStill',s)
    def test_modes_are_explicit_real_render_props(self):s=(SUPPORT/'remotion_raster_capture.cjs').read_text();self.assertIn('inputProps:{__bieRasterMode:mode}',s);self.assertIn("['baseline','isolated','muted']",s);self.assertIn("shot('repeat')",s)
    def test_pinned_renderer_and_mode_drift_check(self):s=(SUPPORT/'remotion_raster_capture.cjs').read_text();self.assertIn('CAPTURE_PIN_MISMATCH',s);self.assertIn('CAPTURE_DOM_MODE_DRIFT',s);self.assertIn('CAPTURE_DOM_NONDETERMINISM',s)
    def test_new_counterfactual_result_required_for_witness(self):s=inspect.getsource(produce_actual_paint);self.assertIn("data.get('counterfactual')",s);self.assertIn("quality['passed'] and raster['passed']",s);self.assertIn('REAL_SCOPE',s)
    def test_real_producer_keeps_kernel_policy(self):s=inspect.getsource(produce_actual_paint);self.assertIn('run_isolated',s);self.assertNotIn('no-sandbox',s);self.assertNotIn('measure_raster_scene',s)
    def test_diagnostic_report_not_witness(self):self.assertRaisesRegex(ValueError,'WITNESS_REQUIRED',require_actual_witness,{'scope':DIAGNOSTIC_SCOPE,'passed':True},'a'*64)
    def test_helper_uses_selected_subtree_and_restores_priorities(self):s=(SUPPORT/'raster_modes.js').read_text();self.assertIn('getPropertyPriority',s);self.assertIn("setProperty('visibility', 'hidden', 'important')",s);self.assertIn('changed.reverse()',s)
    def test_helper_typescript_with_explicit_stub_declarations(self):
        # Actual installed tsc; ONLY helper typing against explicit declarations,
        # not a full pinned React/Remotion compile or runtime.
        with tempfile.TemporaryDirectory() as td:
            p=Path(td);(p/'src').mkdir()
            source=capture_entry_h8(req(),'(options:unknown)=>[]','(options:unknown)=>[]')
            (p/'entry.tsx').write_text('declare function rasterModeImpl(o:unknown):unknown;\n'+source)
            (p/'src/Scene.tsx').write_text('import React from "react";export const Scene:React.FC=()=>null;')
            (p/'explicit-test-doubles.d.ts').write_text('''declare namespace JSX {interface IntrinsicElements {[tag:string]:any;}}
declare namespace React { type FC<P={}>=(props:P)=>any; function useMemo<T>(f:()=>T,deps:unknown[]):T; function useLayoutEffect(f:()=>void|(()=>void),deps:unknown[]):void; }
declare module "react" { export = React; }
declare module "remotion" { export const Composition:React.FC<any>;export function registerRoot(c:React.FC):void;export function useCurrentFrame():number;export function getInputProps():unknown;export function delayRender(s:string):number;export function continueRender(h:number):void;export function cancelRender(e:unknown):void; }
''')
            (p/'tsconfig.json').write_text(json.dumps({'compilerOptions':{'strict':True,'noEmit':True,'target':'ES2020','module':'CommonJS','jsx':'react','esModuleInterop':True},'include':['**/*.tsx','*.d.ts']}))
            r=subprocess.run(['tsc','--project',str(p/'tsconfig.json')],capture_output=True,text=True,timeout=30);self.assertEqual(r.returncode,0,r.stdout+r.stderr)
    def test_actual_producer_rejects_unpublished_input(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td);self.assertRaises(ValueError,produce_actual_paint,p,p/'out',node=shutil.which('node'),browser='/usr/bin/chromium',target=BROWSER)
    def test_missing_dependencies_do_not_run_actual_controller(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td);publish_h3_scene(raw_text(),p/'s',target=BROWSER)
            with self.assertRaises(ValueError):produce_actual_paint(p/'s',p/'out',node=shutil.which('node'),browser='/usr/bin/chromium',target=BROWSER)
            self.assertFalse((p/'out/captured.mp4').exists())
