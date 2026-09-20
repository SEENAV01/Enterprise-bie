"""Actual Node controller exercised with explicitly fake renderer packages.

These tests verify call/identity/failure plumbing ONLY. Dummy PNG/media bytes
cannot pass real raster validation and must never be reported as a render.
"""
import json, subprocess, tempfile, unittest
from pathlib import Path
from copy import deepcopy
from tests.compiler.test_comp_h8_005 import req,SUPPORT

FAKE_RENDERER=r'''
const fs=require('node:fs');const req=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
exports.openBrowser=async()=>({close:async()=>{}});
exports.selectComposition=async()=>({width:req.width,height:req.height,fps:req.fps,durationInFrames:req.frame_count});
exports.renderStill=async o=>{
 const mode=o.inputProps.__bieRasterMode;
 fs.appendFileSync(req.output+'/calls.jsonl',JSON.stringify({frame:o.frame,mode})+'\n');
 fs.writeFileSync(o.output,'EXPLICIT_RENDERER_DOUBLE_NOT_PNG');
 const inv=req.rasterTargets.map(t=>({target_id:t.target_id,visible:true,unresolved_effect:false,box:[0,0,20,20]}));
 if(req.test_case==='mode-drift'&&mode.kind==='muted')inv[0].box[0]=1;
 const m={nonce:req.test_case==='wrong-nonce'?'wrong':req.nonce,frame:o.frame,
  fonts_ready:true,records:[],paint_records:[],raster:{mode,inventory:inv,fonts_ready:req.test_case!=='fonts',image_errors:[]}};
 if(req.test_case==='missing')return;
 o.onBrowserLog({type:'log',text:'BIE_PAINT_V1:'+JSON.stringify(m)});
 if(req.test_case==='nondeterministic'){m.records=[{changed:true}];o.onBrowserLog({type:'log',text:'BIE_PAINT_V1:'+JSON.stringify(m)});}
};
exports.renderMedia=async o=>fs.writeFileSync(o.outputLocation,'EXPLICIT_TEST_DOUBLE_NOT_VIDEO');
'''
class ActualControllerPlumbingTests(unittest.TestCase):
    def run_case(self,case='ok',pin='4.0.506'):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup);root=Path(tmp.name);out=root/'out';out.mkdir();(root/'package.json').write_text('{}')
        for name in ('remotion','@remotion/renderer','@remotion/bundler'):
            p=root/'node_modules'/name;p.mkdir(parents=True);(p/'package.json').write_text(json.dumps({'name':name,'version':pin,'main':'index.js'}))
            (p/'index.js').write_text(FAKE_RENDERER if name.endswith('renderer') else 'exports.bundle=async()=>"EXPLICIT_TEST_DOUBLE_BUNDLE";')
        r=req();r.update(workspace=str(root),output=str(out),browser='/explicit-test-double',remotion_version='4.0.506',test_case=case,scene_sha256='b'*64,manifest_sha256='a'*64)
        p=root/'request.json';p.write_text(json.dumps(r));run=subprocess.run(['node',str(SUPPORT/'remotion_raster_capture.cjs'),str(p)],capture_output=True,text=True,timeout=15)
        return run,out
    def test_calls_every_frame_and_every_mode(self):
        r,p=self.run_case();self.assertEqual(r.returncode,0,r.stderr);calls=[json.loads(x) for x in (p/'calls.jsonl').read_text().splitlines()];self.assertEqual(len(calls),10)
        self.assertEqual([x['mode']['kind'] for x in calls[:5]],['full','baseline','isolated','muted','full'])
    def test_output_has_full_contract_but_cannot_authorize(self):
        r,p=self.run_case();self.assertEqual(r.returncode,0);data=json.loads((p/'RESULT.json').read_text());self.assertFalse(data['accepted']);self.assertEqual(len(data['counterfactual']['frames']),2);self.assertFalse((p/'captured.mp4').read_bytes().startswith(b'\x00\x00'))
    def test_pin_mismatch_blocks(self):r,p=self.run_case(pin='0.0.0');self.assertNotEqual(r.returncode,0);self.assertIn('PIN_MISMATCH',r.stderr);self.assertFalse((p/'RESULT.json').exists())
    def test_missing_measurement_blocks(self):r,p=self.run_case('missing');self.assertNotEqual(r.returncode,0);self.assertIn('MEASUREMENT_MISSING',r.stderr)
    def test_wrong_nonce_ignored_and_blocks(self):r,p=self.run_case('wrong-nonce');self.assertNotEqual(r.returncode,0);self.assertIn('MEASUREMENT_MISSING',r.stderr)
    def test_nondeterministic_observer_blocks(self):r,p=self.run_case('nondeterministic');self.assertNotEqual(r.returncode,0);self.assertIn('NONDETERMINISM',r.stderr)
    def test_mode_changes_geometry_blocks(self):r,p=self.run_case('mode-drift');self.assertNotEqual(r.returncode,0);self.assertIn('MODE_DRIFT',r.stderr)
    def test_unresolved_fonts_blocks(self):r,p=self.run_case('fonts');self.assertNotEqual(r.returncode,0);self.assertIn('ASSET_READINESS',r.stderr)
