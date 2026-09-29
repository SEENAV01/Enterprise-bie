from h5_helpers import *
from bie.qa.media_runtime_v2.native import *
from bie.qa.media_runtime_v2.stream import inspect
NEEDED=('source-scene','checked-scene','input-manifest','render-recipe','toolchain','isolation','render-log')
class NativeAV(Case):
    def seed(self):
        video=encode(self.root);p=AVPolicy('Composition',hashlib.sha256(b'{}').hexdigest(),REV,NEEDED);b=bind(p)
        sp=StreamPolicy(64,48,'12',12,chunk_frames=4,sample_frames=(0,4,11));fm=tool('ffmpeg');fp=tool('ffprobe')
        stream=inspect(self.root,video,bind(sp),sp,ffmpeg=fm,ffprobe=fp)
        n=dict(schema_version='bie.render-receipt.v1',run_id=b.run_id,mode='full',composition_id='Composition',passed=True,failure_code=None,errors=[],output_path=video.path,expected_frames=12,media=None,input_sha256='1'*64,recipe_sha256='2'*64,evidence_directory='render-evidence/run-h5',execution_kind='LOCAL_REMOTION_CLI',process_started=True,artifact_sha256=video.sha256,artifact_size_bytes=video.size,accepted=False)
        nr=save(self.root,'native.json',n,'native');refs=tuple(ref(self.root,'evidence/'+k+'.json',b'{}',k) for k in NEEDED)
        return video,p,b,sp,fm,fp,stream,n,nr,refs
    def run_case(self,mutate=None,redecode=True):
        video,p,b,sp,fm,fp,s,n,nr,rs=self.seed()
        if mutate:mutate(n,s)
        nr=save(self.root,'native.json',n,'native')
        return inspect_native_av(self.root,nr,video,s,b,p,evidence_refs=rs,stream_policy=sp if redecode else None,ffmpeg=fm,ffprobe=fp,now=NOW)
    def test_actual_redecode_still_requires_native_attestation(self):
        r=self.run_case();self.assertTrue(r['details']['actual_media_redecoded']);self.assertEqual(r['report']['status'],'REVIEW_REQUIRED');self.assertFalse(r['details']['native_provenance_authenticated'])
    def test_persisted_json_stream_receipt_replays(self):
        r=self.run_case(lambda n,s:s.update(json.loads(canonical_bytes(s))));self.assertTrue(r['details']['actual_media_redecoded'])
    def test_materialized_png_receipt_replays(self):
        v,p,b,sp,fm,fp,s,n,nr,rs=self.seed();s=inspect(self.root,v,bind(sp),sp,ffmpeg=fm,ffprobe=fp,samples_dir=self.root/'samples')
        r=inspect_native_av(self.root,nr,v,json.loads(canonical_bytes(s)),b,p,evidence_refs=rs,stream_policy=sp,ffmpeg=fm,ffprobe=fp,now=NOW);self.assertTrue(r['details']['actual_media_redecoded'])
    def test_signed_or_unsigned_receipt_not_a_substitute_for_decoder(self):self.has(self.run_case(redecode=False),'H5_AV_FRESH_REDECODE_REQUIRED')
    def test_injected_renderer_is_not_native(self):self.has(self.run_case(lambda n,s:n.update(execution_kind='INJECTED_TEST_RUNNER')),'H5_NATIVE_FULL_RENDER_REQUIRED')
    def test_smoke_is_not_full(self):self.has(self.run_case(lambda n,s:n.update(mode='smoke')),'H5_NATIVE_FULL_RENDER_REQUIRED')
    def test_failed_native_execution(self):self.has(self.run_case(lambda n,s:n.update(passed=False,failure_code='FAILED',errors=['failure'])),'H5_NATIVE_FULL_RENDER_REQUIRED')
    def test_changed_video_identity(self):
        with self.assertRaisesRegex(ContractError,'VIDEO_NATIVE_MEDIA_BINDING'):self.run_case(lambda n,s:n.update(artifact_sha256='0'*64))
    def test_false_native_acceptance_flag(self):
        with self.assertRaisesRegex(ContractError,'VIDEO_NATIVE_ACCEPTANCE'):self.run_case(lambda n,s:n.update(accepted=True))
    def test_wrong_native_run(self):
        with self.assertRaisesRegex(ContractError,'VIDEO_NATIVE_RUN'):self.run_case(lambda n,s:n.update(run_id='foreign'))
    def test_stale_stream_receipt_requires_replay(self):
        with self.assertRaisesRegex(ContractError,'H5_AV_STREAM_REPLAY_MISMATCH'):self.run_case(lambda n,s:s['details'].update(frames=11))
    def test_foreign_stream_evidence_rejected(self):
        with self.assertRaisesRegex(ContractError,'H5_AV_STREAM_REPLAY_MISMATCH'):self.run_case(lambda n,s:s['report']['binding'].update(run_id='foreign'))
    def test_empty_required_lineage_cannot_reduce_scope(self):
        with self.assertRaisesRegex(ContractError,'H5_NATIVE_REQUIRED_LINEAGE'):AVPolicy('x','a'*64,REV,('one',))
    def test_wrong_source_scene(self):
        v,p,b,sp,fm,fp,s,n,nr,refs=self.seed();p=replace(p,scene_sha256='f'*64);b=bind(p)
        r=inspect_native_av(self.root,nr,v,s,b,p,evidence_refs=refs,stream_policy=sp,ffmpeg=fm,ffprobe=fp,now=NOW);self.has(r,'H5_AV_SCENE_BYTES')
    def test_missing_lineage_bytes(self):
        v,p,b,sp,fm,fp,s,n,nr,refs=self.seed();r=inspect_native_av(self.root,nr,v,s,b,p,evidence_refs=refs[:-1],stream_policy=sp,ffmpeg=fm,ffprobe=fp,now=NOW);self.has(r,'H5_AV_EVIDENCE_INVENTORY')
class Checkout(Case):
    def seed(self):
        paths=('scripts/compile_scene_checked.py','scripts/run_comp_render.py')
        for p in paths:ref(self.root,p,b'# Synthetic nonexecuting inventory fixture\n',p.split('/')[-1])
        profile=NativeProfile(REV,tuple((p,hash_file(self.root/p)[0]) for p in paths),tool('python'))
        return profile
    def test_checkout_inventory_success_not_native_execution(self):
        p=self.seed();r=preflight(self.root,p);self.assertEqual(r['status'],'READY_FOR_TRUSTED_INVOCATION');self.assertFalse(r['native_executed'])
    def test_missing_native_source_stops(self):
        p=self.seed();(self.root/p.files[0][0]).unlink();self.assertEqual(preflight(self.root,p)['status'],'BLOCKED')
    def test_changed_native_source_stops(self):
        p=self.seed();(self.root/p.files[0][0]).write_text('bad');self.assertEqual(preflight(self.root,p)['status'],'BLOCKED')
    def test_no_execution_without_opt_in(self):
        p=self.seed()
        with self.assertRaisesRegex(ContractError,'H5_NATIVE_EXECUTION_OPT_IN'):run_native_pipeline(self.root,p,self.root/'scene.json',self.root/'out',{})
    def test_injection_argument_is_forbidden(self):
        p=self.seed();(self.root/'scene.json').write_text('{}')
        with self.assertRaisesRegex(ContractError,'H5_NATIVE_INJECTED_OR_PARTIAL_REQUEST'):run_native_pipeline(self.root,p,self.root/'scene.json',self.root/'out',{'composition':{},'runner':'fake'},allow_trusted_execution=True)
    def test_destination_never_overwritten(self):
        p=self.seed();(self.root/'scene.json').write_text('{}');(self.root/'out').mkdir()
        with self.assertRaisesRegex(ContractError,'H5_NATIVE_OUTPUT_EXISTS'):run_native_pipeline(self.root,p,self.root/'scene.json',self.root/'out',{'composition':{}},allow_trusted_execution=True)
    def test_required_entrypoints(self):
        with self.assertRaisesRegex(ContractError,'H5_NATIVE_ENTRYPOINTS'):NativeProfile(REV,(('a','a'*64),('b','b'*64)),tool('python'))

class CompileArguments(Case):
    def test_target_passed_to_canonical_compile_entrypoint(self):
        from unittest.mock import patch
        p=Checkout.seed(self);(self.root/'scene.json').write_text('{}');seen=[]
        def diagnostic_run(argv,cwd,timeout):
            # Mocked command observation, NOT a native execution receipt.
            seen.append(argv);return {'exit_code':1,'stdout':'SYNTHETIC compile failure','stderr':''}
        with patch('bie.qa.media_runtime_v2.native._run',diagnostic_run):
            r=run_native_pipeline(self.root,p,self.root/'scene.json',self.root/'out',{'composition':{'width':1280,'height':720,'fps':24}},allow_trusted_execution=True,motion_preference='reduced')
        self.assertEqual(r['status'],'BLOCKED');self.assertFalse(r['native_pipeline_success']);self.assertIn('--width',seen[0]);self.assertEqual(seen[0][seen[0].index('--width')+1],'1280');self.assertEqual(seen[0][-1],'reduced')
    def test_noninteger_native_cli_fps_is_not_rounded(self):
        p=Checkout.seed(self);(self.root/'scene.json').write_text('{}')
        with self.assertRaises(ContractError):run_native_pipeline(self.root,p,self.root/'scene.json',self.root/'out',{'composition':{'width':1280,'height':720,'fps':'30000/1001'}},allow_trusted_execution=True)
