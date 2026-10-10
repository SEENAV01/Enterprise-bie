"""Bounded media policy tests; Node doubles do NOT claim native rendered PASS."""
import ast
from copy import deepcopy
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
import unittest

from tests.compiler.m1_support import prepared, admitted, TARGET
from tests.compiler import test_m1_capture_diagnostics as capture_controls

ROOT=Path(__file__).resolve().parents[2]
HELPER=ROOT/'bie/compiler/qa_support/bounded_media_threads.cjs'
POLICY={'schema':'bie.comp-m1.media-threads/1','profile':'producer-motion-v1',
    'remotion_version':'4.0.506','admission_id':'a'*64,'decoder_threads':1,
    'encoder_threads':1,'filter_threads':1}
PRE=['-r','24','-f','image2pipe','-s','960x640','-vcodec','png','-i','-',
    '-c:v','libx264','-pix_fmt','yuv420p','-crf','18','-y','synthetic-output.mp4']
STITCH=['-i','synthetic-input.mp4','-c:v','copy','-metadata','title=synthetic','-y','synthetic-final.mp4']


def run_node(body):
    # Only synthetic argument fixtures enter this plumbing harness. No real
    # command/stdout/stderr/private result is collected by the production helper.
    code='const api=require('+json.dumps(str(HELPER))+');const p='+json.dumps(POLICY)+';const pre='+json.dumps(PRE)+';const stitch='+json.dumps(STITCH)+';'+body
    result=subprocess.run(['node','-e',code],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,timeout=15)
    if result.returncode:raise AssertionError('M1_MEDIA_NODE_CONTROL_FAILED')
    return json.loads(result.stdout)


class MediaThreadPolicy(unittest.TestCase):
    def test_explicit_closed_policy_frozen_and_not_mutated(self):
        v=run_node('const old=JSON.stringify(p),q=api.validatePolicy(p);console.log(JSON.stringify({frozen:Object.isFrozen(q),same:JSON.stringify(q)===old}));')
        self.assertEqual(v,{'frozen':True,'same':True})

    def test_unknown_schema_profile_pin_admission_rejected(self):
        for key,value in [('schema','unknown'),('profile','web'),('remotion_version','4.0.507'),('admission_id','foreign')]:
            with self.subTest(key=key):
                self.assertTrue(run_node('p['+json.dumps(key)+']='+json.dumps(value)+';let rejected=false;try{api.validatePolicy(p)}catch(e){rejected=e.message==="M1_MEDIA_THREAD_POLICY_REJECTED"}console.log(JSON.stringify(rejected));'))

    def test_unknown_keys_or_self_claimed_safe_flags_rejected(self):
        for key in ('accepted','reduced_safe','stderr','threads'):
            self.assertTrue(run_node('p['+json.dumps(key)+']=true;let r=false;try{api.validatePolicy(p)}catch(e){r=true}console.log(JSON.stringify(r));'))

    def test_boolean_coercion_zero_overflow_threads_rejected(self):
        for value in (True,False,0,2,'1',None):
            self.assertTrue(run_node('p.decoder_threads='+json.dumps(value)+';let r=false;try{api.validatePolicy(p)}catch(e){r=true}console.log(JSON.stringify(r));'))

    def test_source_args_preserved_in_order_and_unmodified(self):
        v=run_node('const old=JSON.stringify(pre),a=api.lowerArguments("pre-stitcher",pre);const cleaned=[];for(let i=0;i<a.length;i++){if(["-filter_threads","-filter_complex_threads","-threads"].includes(a[i]))i++;else cleaned.push(a[i])}console.log(JSON.stringify({same:JSON.stringify(pre)===old,exact:JSON.stringify(cleaned)===old}));')
        self.assertEqual(v,{'same':True,'exact':True})

    def test_decoder_flag_before_input_and_encoder_before_output(self):
        a=run_node('console.log(JSON.stringify(api.lowerArguments("pre-stitcher",pre)));')
        self.assertEqual(a[a.index('-i')-2:a.index('-i')],['-threads','1'])
        self.assertEqual(a[-4:],['-threads','1','-y','synthetic-output.mp4'])

    def test_both_filter_pool_flags_global_before_input(self):
        a=run_node('console.log(JSON.stringify(api.lowerArguments("pre-stitcher",pre)));')
        self.assertEqual(a[:4],['-filter_threads','1','-filter_complex_threads','1'])

    def test_stitcher_copy_codec_and_metadata_unchanged(self):
        a=run_node('console.log(JSON.stringify(api.lowerArguments("stitcher",stitch)));')
        self.assertEqual(a[a.index('-c:v')+1],'copy')
        self.assertEqual(a[a.index('-metadata')+1],'title=synthetic')

    def test_unknown_callback_type_rejected(self):
        self.assertTrue(run_node('let r=false;try{api.lowerArguments("audio",pre)}catch(e){r=true}console.log(JSON.stringify(r));'))

    def test_actual_pinned_numeric_fps_preserved_without_coercion(self):
        value=run_node('pre[1]=24;const a=api.lowerArguments("pre-stitcher",pre);console.log(JSON.stringify({fps:a[a.indexOf("-r")+1],type:typeof a[a.indexOf("-r")+1]}));')
        self.assertEqual(value,{'fps':24,'type':'number'})

    def test_unapproved_numeric_option_or_nonfinite_fps_rejected(self):
        for body in ('pre[1]=NaN;','pre[1]=Infinity;','pre[1]=true;','pre[1]=30;','pre[5]=24;'):
            self.assertTrue(run_node(body+'let r=false;try{api.lowerArguments("pre-stitcher",pre)}catch(e){r=true}console.log(JSON.stringify(r));'))

    def test_existing_thread_options_never_overridden(self):
        for option in ('-threads','-threads:v','-threads=2','-filter_threads','-filter_complex_threads'):
            self.assertTrue(run_node('pre.splice(0,0,'+json.dumps(option)+',"2");let r=false;try{api.lowerArguments("pre-stitcher",pre)}catch(e){r=true}console.log(JSON.stringify(r));'))

    def test_multiple_or_missing_inputs_fail_closed(self):
        for body in ('pre.splice(8,2);','pre.splice(8,0,"-i","foreign");'):
            self.assertTrue(run_node(body+'let r=false;try{api.lowerArguments("pre-stitcher",pre)}catch(e){r=true}console.log(JSON.stringify(r));'))

    def test_unsupported_codec_and_nonpipe_pre_stitcher_rejected(self):
        for body in ('pre[pre.indexOf("-c:v")+1]="vp9";','pre[pre.indexOf("-i")+1]="foreign";'):
            self.assertTrue(run_node(body+'let r=false;try{api.lowerArguments("pre-stitcher",pre)}catch(e){r=true}console.log(JSON.stringify(r));'))

    def test_malformed_nonstring_null_or_nul_arguments_rejected(self):
        for value in (None,True,1,'\0'):
            self.assertTrue(run_node('pre[0]='+json.dumps(value)+';let r=false;try{api.lowerArguments("pre-stitcher",pre)}catch(e){r=true}console.log(JSON.stringify(r));'))

    def test_argument_count_and_text_budgets_fail_closed(self):
        for body in ('pre=new Array(257).fill("x");','pre[0]="x".repeat(16385);','pre=new Array(100).fill("x".repeat(1000));'):
            self.assertTrue(run_node(body.replace('pre=','const oversized=')+'let r=false;try{api.lowerArguments("pre-stitcher",'+('oversized' if 'pre=' in body else 'pre')+')}catch(e){r=true}console.log(JSON.stringify(r));'))

    def test_unrecognized_output_shape_rejected(self):
        self.assertTrue(run_node('pre[pre.length-2]="-unknown";let r=false;try{api.lowerArguments("pre-stitcher",pre)}catch(e){r=true}console.log(JSON.stringify(r));'))

    def test_no_completion_without_mandatory_stitcher(self):
        self.assertTrue(run_node('const b=api.createOverride(p);b.override({type:"pre-stitcher",args:pre});let r=false;try{b.completed()}catch(e){r=true}console.log(JSON.stringify(r));'))

    def test_both_callbacks_recorded_exactly_once(self):
        v=run_node('const b=api.createOverride(p);b.override({type:"pre-stitcher",args:pre});b.override({type:"stitcher",args:stitch});console.log(JSON.stringify(b.completed()));')
        self.assertEqual(v,{**POLICY,'pre_stitcher_calls':1,'stitcher_calls':1})

    def test_native_optional_pre_stitcher_absence_recorded_not_fabricated(self):
        v=run_node('const b=api.createOverride(p);b.override({type:"stitcher",args:stitch});console.log(JSON.stringify(b.completed()));')
        self.assertEqual(v,{**POLICY,'pre_stitcher_calls':0,'stitcher_calls':1})

    def test_no_callbacks_cannot_complete(self):
        self.assertTrue(run_node('let r=false;try{api.createOverride(p).completed()}catch(e){r=true}console.log(JSON.stringify(r));'))

    def test_painter_completion_requires_exact_shape_integer_types_and_policy(self):
        tree=ast.parse((ROOT/'bie/compiler/real_paint.py').read_text())
        node,=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_validate_media_thread_execution']
        from bie.compiler.qa_common import CompilerQAError
        ns={'CompilerQAError':CompilerQAError}
        exec(compile(ast.Module([node],type_ignores=[]),'actual_media_execution_validator','exec'),ns)
        check=ns[node.name]
        for count in (0,1):
            row={**POLICY,'pre_stitcher_calls':count,'stitcher_calls':1}
            self.assertIs(check(row,POLICY),row)
        for key in ('pre_stitcher_calls','stitcher_calls','decoder_threads','encoder_threads','filter_threads'):
            for value in (True,False,1.0,'1',None,2,-1):
                with self.subTest(key=key,value=value),self.assertRaises(CompilerQAError):
                    check({**POLICY,'pre_stitcher_calls':1,'stitcher_calls':1,key:value},POLICY)
        for row in (None,{}, {**POLICY,'pre_stitcher_calls':1,'stitcher_calls':1,'private':'forbidden'},
                    {**POLICY,'pre_stitcher_calls':1,'stitcher_calls':0},
                    {**POLICY,'pre_stitcher_calls':1,'stitcher_calls':1,'admission_id':'b'*64}):
            with self.assertRaises(CompilerQAError):check(row,POLICY)

    def test_duplicate_callback_rejected_not_silent_retry(self):
        self.assertTrue(run_node('const b=api.createOverride(p);b.override({type:"pre-stitcher",args:pre});let r=false;try{b.override({type:"pre-stitcher",args:pre})}catch(e){r=true}console.log(JSON.stringify(r));'))
        self.assertTrue(run_node('const b=api.createOverride(p);b.override({type:"pre-stitcher",args:pre});try{b.override({type:"pre-stitcher",args:pre})}catch(e){}b.override({type:"stitcher",args:stitch});let r=false;try{b.completed()}catch(e){r=true}console.log(JSON.stringify(r));'))

    def test_unknown_callback_fields_rejected(self):
        self.assertTrue(run_node('let r=false;try{api.createOverride(p).override({type:"pre-stitcher",args:pre,source:"private"})}catch(e){r=true}console.log(JSON.stringify(r));'))

    def test_safe_completion_has_no_arguments_paths_or_content(self):
        v=run_node('const b=api.createOverride(p);pre[pre.length-1]="FAKE_PRIVATE_SOURCE_TOKEN";b.override({type:"pre-stitcher",args:pre});b.override({type:"stitcher",args:stitch});console.log(JSON.stringify(b.completed()));')
        self.assertNotIn('FAKE_PRIVATE',json.dumps(v));self.assertEqual(set(v),set(POLICY)|{'pre_stitcher_calls','stitcher_calls'})

    def test_helper_has_no_spawn_io_or_sensitive_object_traversal(self):
        source=HELPER.read_text()
        for forbidden in ('child_process','readFile','writeFile','console.','stderr','stdout','process.env'):
            self.assertNotIn(forbidden,source)

    def test_legacy_controller_plumbing_still_passes_without_policy(self):
        helper=capture_controls.CaptureControllerPlumbing();helper._cleanups=[]
        try:
            code,out=helper.run_case('success');self.assertEqual(code,0)
            self.assertNotIn('media_thread_execution',json.loads((out/'RESULT.json').read_text()))
        finally:helper.doCleanups()


def selector():
    # Actual pure admission function, not a fake renderer or fabricated approval.
    tree=ast.parse((ROOT/'bie/compiler/real_paint.py').read_text())
    node,=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_governed_media_thread_policy']
    from bie.compiler.qa_common import CompilerQAError
    namespace={'__package__':'bie.compiler','CompilerQAError':CompilerQAError}
    exec(compile(ast.Module([node],type_ignores=[]),'actual_media_policy_selector','exec'),namespace)
    return namespace[node.name]


class MediaSourceAdmission(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.fixture,cls.cases=prepared()
    @classmethod
    def tearDownClass(cls):cls.fixture.tearDown()
    def setUp(self):
        self.fixture.p=replace(self.fixture.p,expires_at=time.time()+900)
        self.fixture.credentials.grant(self.fixture.token,self.fixture.p)

    def test_all_actual_task035_families_require_current_admission(self):
        for family,case in self.cases.items():
            with self.subTest(family=family),admitted(self.fixture,case) as (raw,bound,_):
                original=deepcopy(raw);p=selector()(raw,TARGET)
                self.assertEqual(p['admission_id'],raw['metadata']['producer_motion']['admission_id'])
                self.assertEqual(p['schema'],POLICY['schema']);self.assertEqual(raw,original)
                self.assertEqual(p['decoder_threads'],1)

    def test_explicit_envelope_outside_authority_rejected(self):
        with admitted(self.fixture,self.cases['cellular']) as (raw,_,_):copy=deepcopy(raw)
        with self.assertRaises(ValueError):selector()(copy,TARGET)

    def test_changed_recomputed_content_cannot_select_policy(self):
        with admitted(self.fixture,self.cases['quantitative']) as (raw,_,_):
            bad=deepcopy(raw);bad['elements'][0]['props']['values'][0]+=1
            with self.assertRaises(ValueError):selector()(bad,TARGET)

    def test_unversioned_empty_document_keeps_legacy_path(self):
        self.assertIsNone(selector()({'tracks':[],'metadata':{}},TARGET))

    def test_opaque_legacy_annotation_is_not_authority(self):
        self.assertIsNone(selector()({'tracks':[],'metadata':{'producer_motion':{'annotation':'opaque'}}},TARGET))

    def test_changed_parser_render_pin_rejected(self):
        with admitted(self.fixture,self.cases['cellular']) as (raw,_,_):
            with self.assertRaises(ValueError):selector()(raw,replace(TARGET,remotion_version='4.0.507'))


class MediaControllerDispatch(unittest.TestCase):
    """Real controller with declared renderer doubles; no render proof claimed."""
    def execute(self,policy=POLICY,missing_callback=False,optional_pre_absent=False):
        temporary=tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup)
        root=Path(temporary.name);out=root/'out';out.mkdir();(root/'package.json').write_text('{}')
        fake=capture_controls.FAKE
        start=fake.index('exports.renderMedia=')
        fake=fake[:start]+'''exports.renderMedia=async o=>{
if(o.ffmpegOverride){
 const pre=['-r','24','-f','image2pipe','-s','960x640','-vcodec','png','-i','-','-c:v','libx264','-pix_fmt','yuv420p','-y','synthetic.mp4'];
 const stitch=['-i','synthetic.mp4','-c:v','copy','-metadata','title=synthetic','-y','synthetic-final.mp4'];
 const a=req.optional_pre_absent?null:o.ffmpegOverride({type:'pre-stitcher',args:pre});
 if(!req.missing_callback){const b=o.ffmpegOverride({type:'stitcher',args:stitch});if(!b.includes('-filter_threads'))throw new Error('fixture');}
 if(a&&!a.includes('-filter_complex_threads'))throw new Error('fixture');
}fs.writeFileSync(o.outputLocation,'EXPLICIT_DOUBLE_NOT_VIDEO');};'''
        for name in ('remotion','@remotion/renderer','@remotion/bundler'):
            folder=root/'node_modules'/name;folder.mkdir(parents=True)
            (folder/'package.json').write_text(json.dumps({'name':name,'version':'4.0.506','main':'index.js'}))
            (folder/'index.js').write_text(fake if name.endswith('renderer') else 'exports.bundle=async()=>"EXPLICIT_DOUBLE_BUNDLE";')
        req={'workspace':str(root),'output':str(out),'browser':'explicit-double','remotion_version':'4.0.506',
            'test_case':'success','nonce':'SYNTHETIC','manifest_sha256':'a'*64,'scene_sha256':'b'*64,
            'composition_id':'Test','width':640,'height':360,'fps':4,'frame_count':2,
            'rasterTargets':[{'target_id':'synthetic-target'}],'equationFonts':{},'missing_callback':missing_callback,
            'optional_pre_absent':optional_pre_absent}
        if policy is not None:req['media_thread_policy']=policy
        request=root/'request.json';request.write_text(json.dumps(req))
        result=subprocess.run(['node',str(capture_controls.CONTROLLER),str(request)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=15)
        return result.returncode,out

    def test_new_policy_real_controller_consumes_both_callbacks(self):
        code,out=self.execute();self.assertEqual(code,0)
        data=json.loads((out/'RESULT.json').read_text())
        self.assertEqual(data['media_thread_execution'],{**POLICY,'pre_stitcher_calls':1,'stitcher_calls':1})

    def test_missing_callback_rejects_no_paint_success_and_closes_browser(self):
        code,out=self.execute(missing_callback=True);self.assertEqual(code,2)
        self.assertFalse((out/'RESULT.json').exists());self.assertEqual((out/'closed.txt').read_text(),'closed')

    def test_native_optional_pre_absence_real_controller_records_actual_zero(self):
        code,out=self.execute(optional_pre_absent=True);self.assertEqual(code,0)
        self.assertEqual(json.loads((out/'RESULT.json').read_text())['media_thread_execution'],
            {**POLICY,'pre_stitcher_calls':0,'stitcher_calls':1})

    def test_unknown_policy_cannot_fallback_to_legacy(self):
        bad={**POLICY,'schema':'unknown'};code,out=self.execute(policy=bad)
        self.assertEqual(code,2);self.assertFalse((out/'RESULT.json').exists())
        self.assertEqual((out/'closed.txt').read_text(),'closed')

    def test_explicit_absence_preserves_legacy_result_shape(self):
        code,out=self.execute(policy=None);self.assertEqual(code,0)
        self.assertNotIn('media_thread_execution',json.loads((out/'RESULT.json').read_text()))


class MediaThreadAmendment(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from scripts import compiler_media_thread_amendment as amendment
        cls.amendment=amendment;cls.document=amendment.validate(ROOT)
        temporary=tempfile.TemporaryDirectory();cls.addClassCleanup(temporary.cleanup)
        cls.root=Path(temporary.name)
        paths={amendment.DOCUMENT,amendment.PREVIOUS_DOCUMENT,amendment.CAPTURE_DOCUMENT,amendment.M1_DOCUMENT,
            'manifests/post_dir_integration_004.json','scripts/compiler_cache_source_amendment.py',
            'scripts/compiler_capture_observation_amendment.py'}
        paths.update(r['path'] for r in cls.document['replacements']+cls.document['additions'])
        paths.update(r['preimage'] for r in cls.document['replacements'])
        from scripts import compiler_media_policy_observation_amendment as policy_observation
        policy_doc=policy_observation.validate(ROOT)
        paths.add(policy_observation.DOCUMENT)
        paths.update(r['path'] for r in policy_doc['replacements'])
        paths.update(r['preimage'] for r in policy_doc['replacements'])
        for name in paths:
            p=cls.root/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,p)

    def test_complete_exact_chain_and_git_preimages(self):
        self.assertEqual(self.amendment.validate(self.root),self.document)
        for row in self.document['replacements']:
            original=subprocess.run(['git','show','7c9bafce7cc025f7e134ec6fb46a66197686ec5e:'+row['path']],cwd=ROOT,
                stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,check=True).stdout
            self.assertEqual(original,(self.root/row['preimage']).read_bytes())
            self.assertEqual(sha256(original).hexdigest(),row['original_sha256'])

    def test_every_active_addition_and_preimage_tamper_rejected(self):
        for row in self.document['replacements']+self.document['additions']:
            for key in ['path']+(['preimage'] if 'preimage' in row else []):
                p=self.root/row[key];before=p.read_bytes()
                try:
                    p.write_bytes(before+b'UNAUTHORIZED\n')
                    with self.assertRaises(ValueError):self.amendment.validate(self.root)
                finally:p.write_bytes(before)

    def test_document_recomputed_hash_extra_duplicate_scope_rejected(self):
        p=self.root/self.amendment.DOCUMENT;before=p.read_bytes()
        try:
            for variant in ('extra','duplicate','bless'):
                value=deepcopy(self.document)
                if variant=='bless':value['additions'][0]['active_sha256']='f'*64
                else:
                    row=deepcopy(value['replacements'][0])
                    if variant=='extra':row['path']='bie/compiler/unapproved.py'
                    value['replacements'].append(row)
                p.write_text(json.dumps(value))
                with self.assertRaises(ValueError):self.amendment.validate(self.root)
        finally:p.write_bytes(before)

    def test_historical_original_amendments_and_prior_wiring_pinned(self):
        for name in (self.amendment.M1_DOCUMENT,self.amendment.PREVIOUS_DOCUMENT,self.amendment.CAPTURE_DOCUMENT,
            'scripts/compiler_cache_source_amendment.py','scripts/compiler_capture_observation_amendment.py'):
            p=self.root/name;before=p.read_bytes()
            try:
                p.write_bytes(before+b' ')
                with self.assertRaises(ValueError):self.amendment.validate(self.root)
            finally:p.write_bytes(before)

    def test_unlisted_target_and_wrong_parent_rejected(self):
        with self.assertRaises(ValueError):self.amendment.authenticated_previous_bytes(self.root,'bie/compiler/unlisted.py','a'*64)
        with self.assertRaises(ValueError):self.amendment.authenticated_previous_bytes(self.root,'bie/compiler/real_paint.py','a'*64)

    def test_missing_or_rolled_back_latest_source_fails(self):
        for row in self.document['replacements']:
            p=self.root/row['path'];before=p.read_bytes()
            try:
                p.write_bytes((self.root/row['preimage']).read_bytes())
                with self.assertRaises(ValueError):self.amendment.validate(self.root)
            finally:p.write_bytes(before)

    def test_helper_exact_singleton_not_wildcard_inventory(self):
        self.assertEqual(self.amendment.authenticated_added_paths(self.root),{'bie/compiler/qa_support/bounded_media_threads.cjs'})

    def test_worker_security_calls_and_all_budgets_unchanged(self):
        row,=[r for r in self.document['replacements'] if r['path']=='bie/compiler/real_paint.py']
        before=ast.parse((ROOT/row['preimage']).read_text());after=ast.parse((ROOT/row['path']).read_text())
        for name in ('run_chromium_isolated','isolated_typecheck','WorkerPolicy','inspect_owner_fit','inspect_paint_quality','inspect_counterfactual_capture'):
            def calls(tree):return [ast.dump(n,include_attributes=False) for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id==name]
            self.assertEqual(calls(before),calls(after),name)

    def test_new_inventory_once_and_original_214_files_retained(self):
        from tests.compiler import run_m1_tests as runner
        lanes,inherited=runner.inventory();name='tests/compiler/test_m1_media_threads.py'
        self.assertEqual(lanes['new'].count(name),1);self.assertEqual(len(lanes['native-extra']),214)
        self.assertNotIn(name,lanes['native-extra']);self.assertNotIn(name,lanes['safety']);self.assertNotIn(name,inherited)


if __name__=='__main__':unittest.main()
