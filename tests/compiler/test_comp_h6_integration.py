from copy import deepcopy
from pathlib import Path
from hashlib import sha256
import json,subprocess,sys,tempfile,unittest
from bie.compiler.hardened_scene_compile import compile_h3_scene
from bie.compiler.frame_runtime_contract import plan_frame_runtime
from bie.compiler.frame_state_consumer import runtime_at
from bie.compiler.layout_measurements import inspect_owner_fit
from bie.compiler.content_fit_qa import DECLARED_SCOPE
from tests.compiler.h6_test_support import *


def declared_measurement(r):
    p=plan_frame_runtime(r.effective_document,BIG);records=[]
    for f in range(p['frame_count']):
        v=runtime_at(p,f)
        for e in r.effective_document['elements']:
            eid=e['element_id'];b=e['normalized_box'];box=[b['x']*BIG.width,b['y']*BIG.height,b['width']*BIG.width,b['height']*BIG.height]
            t=v['caption_text'] if eid==p['caption_target_id'] else v['targets'].get(eid,{}).get('text',e['props'].get('text',''))
            records.append({'element_id':eid,'frame':f,'visible':True,'layer_box':box,'ink_boxes':[],'text_boxes':[],
                'rendered_text':[t] if t else [],'scroll_overflow':False,'equation_em_px':None})
    return {'scope':DECLARED_SCOPE,'scene_identity':digest_local(r.effective_document),'manifest_sha256':r.codegen.manifest_sha256,
        'width':BIG.width,'height':BIG.height,'fps':BIG.fps,'frame_count':p['frame_count'],'fonts_ready':True,'browser_errors':[], 'records':records}


def digest_local(p):
    from bie.compiler.qa_common import digest
    return digest(p)

class RuntimeIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p,cls.a=narration_scene();cls.r=compile_h3_scene(cls.p,target=BIG)
    def test_strict_standalone_runtime_typescript_compiles(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'frame-runtime.ts';p.write_text(next(f.content for f in self.r.codegen.files if f.path=='src/runtime/frame-runtime.ts'))
            q=subprocess.run(['tsc',str(p),'--strict','--target','ES2022','--module','commonjs','--outDir',str(Path(td)/'out')],capture_output=True,text=True,timeout=30)
            self.assertEqual(q.returncode,0,q.stdout+q.stderr);self.assertTrue((Path(td)/'out/frame-runtime.js').exists())
    def test_independent_generator_processes_match(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'scene.json';p.write_text(json.dumps(self.p))
            code="import sys,json;from dataclasses import replace;from bie.compiler.qa_scene_compile import CompilerQATarget;from bie.compiler.hardened_scene_compile import compile_h3_scene;t=replace(CompilerQATarget(),compiler_version='1.3.0-comp-h3',width=1280,height=720);print(compile_h3_scene(json.load(open(sys.argv[1])),target=t).codegen.manifest_sha256)"
            r=subprocess.run([sys.executable,'-c',code,str(p)],capture_output=True,text=True,timeout=30,cwd=ROOT)
            self.assertEqual(r.returncode,0,r.stderr);self.assertEqual(r.stdout.strip(),self.r.codegen.manifest_sha256)
    def test_dynamic_measurements_use_current_text(self):
        x=declared_measurement(self.r);report=inspect_owner_fit(x,self.r.effective_document,BIG,self.r.codegen.manifest_sha256);self.assertTrue(report['passed']);self.assertFalse(report['release_authorized'])
    def test_stale_caption_rejected_between_cues(self):
        x=declared_measurement(self.r);next(v for v in x['records'] if v['frame']==24 and v['element_id']=='captions')['rendered_text']=['stale caption']
        q=inspect_owner_fit(x,self.r.effective_document,BIG,self.r.codegen.manifest_sha256);self.assertIn('LAYOUT_RUNTIME_CONTENT_MISMATCH',[f['code'] for f in q['findings']])
    def test_stale_initial_text_rejected_after_event(self):
        x=declared_measurement(self.r);next(v for v in x['records'] if v['frame']==30 and v['element_id']=='e0')['rendered_text']=[self.p['elements'][0]['props']['text']]
        self.assertFalse(inspect_owner_fit(x,self.r.effective_document,BIG,self.r.codegen.manifest_sha256)['passed'])
    def test_incorrectly_hidden_required_text_rejected(self):
        x=declared_measurement(self.r);x['records'][0]['visible']=False
        q=inspect_owner_fit(x,self.r.effective_document,BIG,self.r.codegen.manifest_sha256);self.assertIn('LAYOUT_RUNTIME_VISIBILITY_MISMATCH',[f['code'] for f in q['findings']])
    def test_frame_identity_does_not_include_optional_self_fingerprint(self):
        from bie.compiler.scene_ir_loader import load_scene_ir_payload
        a=self.r.effective_document;b=load_scene_ir_payload(a).document.to_dict()
        self.assertEqual(plan_frame_runtime(a,BIG),plan_frame_runtime(b,BIG))
    def test_reduced_preference_does_not_drop_static_event_or_audio_contracts(self):
        r=compile_h3_scene(self.p,target=BIG,motion_preference='reduced');a=plan_frame_runtime(r.effective_document,BIG);b=plan_frame_runtime(self.r.effective_document,BIG)
        self.assertEqual(a['events'],b['events']);self.assertEqual(a['narration'],b['narration']);self.assertTrue(r.receipt.source_gate_passed)
    def test_audio_failure_handler_requests_fail_not_silent_fallback(self):
        s=next(f.content for f in self.r.codegen.files if f.path=='src/audio/BieNarration.tsx');self.assertIn('onError={(): "fail" => "fail"}',s)
    def test_legacy_fixture_files_unchanged(self):
        inv=json.loads((ROOT/'lineage/hardening_h5/ORIGINAL_MEMBER_HASHES.json').read_text())['members']
        for n,h in inv.items():
            if n.startswith('fixtures/'):self.assertEqual(sha256((ROOT/n).read_bytes()).hexdigest(),h,n)

if __name__=='__main__':unittest.main()
