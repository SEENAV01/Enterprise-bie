import json,sys,tempfile,subprocess,unittest
from pathlib import Path
from copy import deepcopy
from dataclasses import asdict
from bie.compiler.hardened_scene_compile import compile_h3_scene,publish_h3_scene,require_h3_workspace
from bie.compiler.visual_assets import verified_visual_bytes,KEY
from bie.compiler.media_presentation import media_presentations
from bie.compiler.layout_repair import _run_candidates
from bie.compiler.layout_repair_contracts import default_policy
from tests.compiler.h3_test_support import measurement
from tests.compiler.h11_test_support import scene,asset,path,copy_assets,ASSET_ROOT,ROOT,T

class AdoptedMediaWorkflow(unittest.TestCase):
    def test_pristine_media_publication_revalidates(self):
        p=scene()
        with tempfile.TemporaryDirectory() as td:
            dst=Path(td)/'out';publish_h3_scene(p,dst,target=T,asset_root=ASSET_ROOT);r=require_h3_workspace(dst);self.assertTrue(r.source_gate_passed);self.assertEqual((dst/'public'/asset(p)['public_path']).read_bytes(),path(p).read_bytes())
    def test_h10_missing_image_false_success_is_blocked(self):
        p=scene();p['metadata'].pop(KEY)
        with tempfile.TemporaryDirectory() as td:
            dst=Path(td)/'out';self.assertRaisesRegex(ValueError,'MANIFEST_REQUIRED',publish_h3_scene,p,dst,target=T);self.assertFalse(dst.exists())
    def test_actual_bytes_are_required_even_for_valid_source(self):
        p=scene();self.assertTrue(compile_h3_scene(p,target=T).receipt.source_gate_passed)
        with tempfile.TemporaryDirectory() as td:
            dst=Path(td)/'out';self.assertRaisesRegex(ValueError,'ASSET_ROOT_REQUIRED',publish_h3_scene,p,dst,target=T);self.assertFalse(dst.exists())
    def test_tampered_public_asset_blocks_render_revalidation(self):
        p=scene()
        with tempfile.TemporaryDirectory() as td:
            dst=Path(td)/'out';publish_h3_scene(p,dst,target=T,asset_root=ASSET_ROOT);f=dst/'public'/asset(p)['public_path'];f.write_bytes(f.read_bytes()[:-1]+b'x');self.assertRaisesRegex(ValueError,'HASH_MISMATCH',require_h3_workspace,dst)
    def test_missing_public_asset_blocks_render_revalidation(self):
        p=scene()
        with tempfile.TemporaryDirectory() as td:
            dst=Path(td)/'out';publish_h3_scene(p,dst,target=T,asset_root=ASSET_ROOT);(dst/'public'/asset(p)['public_path']).unlink();self.assertRaisesRegex(ValueError,'UNAVAILABLE',require_h3_workspace,dst)
    def test_video_publishes_actual_bytes_and_dependency(self):
        p=scene('trim-video')
        with tempfile.TemporaryDirectory() as td:
            dst=Path(td)/'out';publish_h3_scene(p,dst,target=T,asset_root=ASSET_ROOT);self.assertTrue(require_h3_workspace(dst).source_gate_passed);self.assertIn('@remotion/media',json.loads((dst/'package.json').read_text())['dependencies'])
    def test_source_tampering_still_blocks(self):
        p=scene()
        with tempfile.TemporaryDirectory() as td:
            dst=Path(td)/'out';publish_h3_scene(p,dst,target=T,asset_root=ASSET_ROOT);f=dst/'src/Scene.tsx';f.write_text(f.read_text()+'\n// altered');self.assertRaisesRegex(ValueError,'TAMPERED',require_h3_workspace,dst)
    def test_old_destination_not_overwritten(self):
        p=scene()
        with tempfile.TemporaryDirectory() as td:
            dst=Path(td)/'out';dst.mkdir();(dst/'sentinel').write_text('keep');self.assertRaisesRegex(ValueError,'destination exists',publish_h3_scene,p,dst,target=T,asset_root=ASSET_ROOT);self.assertEqual((dst/'sentinel').read_text(),'keep')
    def test_unrequested_public_file_rejected(self):
        p=scene()
        with tempfile.TemporaryDirectory() as td:
            dst=Path(td)/'out';publish_h3_scene(p,dst,target=T,asset_root=ASSET_ROOT);(dst/'public/extra.png').write_bytes(b'forged');self.assertRaisesRegex(ValueError,'UNINSPECTED_WORKSPACE_FILE',require_h3_workspace,dst)
    def test_source_refs_survive_into_manifest_and_maps(self):
        c=compile_h3_scene(scene('crop-image'),target=T);plan=json.loads(next(f.content for f in c.codegen.files if f.path=='src/bie-visual-media-plan.json'));self.assertEqual(plan['rows'][0]['asset']['source_refs'],['fixture:h11']);self.assertFalse(c.receipt.accepted)
    def test_video_byte_properties_not_overridden_by_scene_props(self):
        p=scene('trim-video');p['elements'][0]['props']['source_duration_ms']=99999;self.assertRaisesRegex(ValueError,'PROPERTY_UNCONSUMED',compile_h3_scene,p,target=T)
    def test_repair_probe_gets_verified_media_bytes(self):
        seen=[];p=scene()
        e=deepcopy(p['elements'][0]);e.update(element_id='text',element_type='text',props={'text':'Asset-backed repair','font_size':18},normalized_box={'x':.1,'y':.85,'width':.5,'height':.1});p['elements'].append(e)
        class Probe:
            def measure(self,result,target,folder,**kw):
                seen.append(kw['asset_bytes']);folder.mkdir();return measurement(result.effective_document,target,result.codegen.manifest_sha256)
        with tempfile.TemporaryDirectory() as td:
            result,_=_run_candidates(p,default_policy(p),T,Probe(),Path(td),asset_root=ASSET_ROOT)
            self.assertTrue(seen);self.assertEqual(next(iter(seen[0].values())),path(p).read_bytes());self.assertIn('visual_asset_verification',result);self.assertFalse(result['release_authorized'])
    def test_same_input_repeated_codegen_is_stable(self):
        p=scene('trim-video');a=compile_h3_scene(p,target=T);b=compile_h3_scene(p,target=T);self.assertEqual(a.codegen.manifest_sha256,b.codegen.manifest_sha256)
    def test_no_actual_render_claim_from_source_publication(self):
        c=compile_h3_scene(scene('crop-image'),target=T);self.assertEqual(c.receipt.real_render_status,'NOT_RUN');self.assertFalse(c.receipt.full_compile_verified)

class GeneratedMediaBehavior(unittest.TestCase):
    def test_actual_ts_emits_correct_source_times_at_every_frame(self):
        from tests.compiler.h11_test_support import diagnostic,nodes
        data=diagnostic(scene('trim-video'),range(24));actual=[]
        for row in data['trees']:
            v=[n for n in nodes(row['tree']) if n['tag']=='video'];actual.append(v[0]['props']['data-bie-source-time'] if v else None)
        self.assertEqual(actual,[None]*6+[f/12 for f in range(12,24)]+[None]*6)
    def test_actual_ts_reverse_seek_is_deterministic(self):
        from tests.compiler.h11_test_support import diagnostic
        a=diagnostic(scene('trim-video'),range(24))['trees'];b=diagnostic(scene('trim-video'),reversed(range(24)))['trees'];self.assertEqual(a,b[::-1])
    def test_root_visibility_matches_media_lifetime(self):
        from tests.compiler.h11_test_support import diagnostic,nodes
        data=diagnostic(scene('trim-video'),[0,6,17,18,23]);got=[]
        for row in data['trees']:
            owner=next(n for n in nodes(row['tree']) if n['props'].get('data-bie-layer-id')=='e0');got.append(owner['props']['style']['visibility'])
        self.assertEqual(got,['hidden','visible','visible','hidden','hidden'])
    def test_generated_crop_positions_have_actual_effect(self):
        from tests.compiler.h11_test_support import diagnostic,nodes
        a=diagnostic(scene('crop-image'),[0])['trees'][0]['tree'];b=diagnostic(scene('full-image'),[0])['trees'][0]['tree']
        ia=next(n for n in nodes(a) if n['tag']=='img');ib=next(n for n in nodes(b) if n['tag']=='img');self.assertNotEqual(ia['props']['style']['left'],ib['props']['style']['left']);self.assertEqual(ia['props']['src'],ib['props']['src'])
    def test_video_state_changes_keep_source_clock(self):
        from tests.compiler.h11_test_support import diagnostic,nodes
        from tests.compiler.h10_test_support import bind
        p=bind(scene('trim-video'),consent=False);data=diagnostic(p,[6,10,17]);v=[next(n for n in nodes(r['tree']) if n['tag']=='video') for r in data['trees']];self.assertEqual([n['props']['data-bie-source-time'] for n in v],[1,16/12,23/12])
    def test_diagnostic_explicitly_denies_remotion_and_audio(self):
        from tests.compiler.h11_test_support import diagnostic
        d=diagnostic(scene('trim-video'),[6]);self.assertFalse(d['real_remotion']);self.assertFalse(d['audio_played']);self.assertFalse(d['accepted'])
