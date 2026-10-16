"""Failure-only guard plumbing/privacy, never actual renderer acceptance."""
import ast
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from tests.compiler import test_m1_capture_diagnostics as capture
from tests.compiler import test_m1_media_threads as threads
from tests.compiler import m1_safe_paint_diagnostics as safe

ROOT=Path(__file__).resolve().parents[2]
CONTROLLER=ROOT/'bie/compiler/qa_support/remotion_raster_capture.cjs'
PHASES={
 'MEDIA_POLICY_CREATE':('POLICY_SHAPE','POLICY_IDENTITY'),
 'MEDIA_CALLBACK_PRE':('REQUEST_SHAPE','ARGUMENT_SHAPE','ARGUMENT_THREADS','ARGUMENT_INPUT','ARGUMENT_OUTPUT','ARGUMENT_CODEC','ARGUMENT_PIPE','CALLBACK_DUPLICATE'),
 'MEDIA_CALLBACK_STITCH':('REQUEST_SHAPE','ARGUMENT_SHAPE','ARGUMENT_THREADS','ARGUMENT_INPUT','ARGUMENT_OUTPUT','ARGUMENT_CODEC','CALLBACK_DUPLICATE'),
 'MEDIA_CALLBACK_UNKNOWN':('REQUEST_SHAPE','CALLBACK_KIND'),
 'MEDIA_POLICY_COMPLETE':('COMPLETION_COUNTS',)}


def row(phase='MEDIA_POLICY_COMPLETE',code='COMPLETION_COUNTS'):
    calls={'create':1,'pre_stitcher':0,'stitcher':0,'unknown_callback':0,'completion':0}
    key={'MEDIA_CALLBACK_PRE':'pre_stitcher','MEDIA_CALLBACK_STITCH':'stitcher',
        'MEDIA_CALLBACK_UNKNOWN':'unknown_callback','MEDIA_POLICY_COMPLETE':'completion'}.get(phase)
    if key:calls[key]=1
    return {**capture.receipt(),'schema':'bie.capture-controller-failure/2',
        'phase':phase,'guard_code':code,'shot_kind':'NONE','policy_calls':calls}


def observed(body):
    source=CONTROLLER.read_text()
    start=source.index('function mediaPolicyPhase(')
    end=source.index('\nfunction reject(',start)
    setup="const observation={schema:'bie.capture-controller-failure/1',phase:'RENDER_MEDIA',guard_code:'NONE_RECORDED'};const policyCalls={create:1,pre_stitcher:0,stitcher:0,unknown_callback:0,completion:0};function mark(p){observation.schema='bie.capture-controller-failure/1';observation.phase=p;observation.guard_code='NONE_RECORDED';}\n"
    result=subprocess.run(['node','-e',setup+source[start:end]+'\n'+body],
        stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,timeout=15)
    if result.returncode:raise AssertionError('POLICY_OBSERVER_CONTROL_BLOCKED')
    return json.loads(result.stdout)


class PolicyGuardSchema(unittest.TestCase):
    def setUp(self):self.native=capture.pure_native_reader()

    def test_all_closed_v2_guard_phase_pairs_valid(self):
        for phase,codes in PHASES.items():
            for code in (*codes,'NONE_RECORDED'):
                with self.subTest(phase=phase,code=code):self.assertIs(self.native.validate(row(phase,code),capture.MANIFEST)['accepted'],False)

    def test_v1_cannot_claim_v2_guards(self):
        value=row();value['schema']='bie.capture-controller-failure/1'
        with self.assertRaises(ValueError):self.native.validate(value,capture.MANIFEST)

    def test_v2_cannot_claim_unversioned_guard(self):
        value=row('RENDER_STILL','NONE_RECORDED')
        with self.assertRaises(ValueError):self.native.validate(value,capture.MANIFEST)

    def test_unknown_or_wrong_phase_guard_fails(self):
        for phase,code in [('MEDIA_POLICY_CREATE','COMPLETION_COUNTS'),('MEDIA_CALLBACK_STITCH','ARGUMENT_PIPE'),('MEDIA_CALLBACK_UNKNOWN','PRIVATE_TEXT')]:
            with self.assertRaises(ValueError):self.native.validate(row(phase,code),capture.MANIFEST)

    def test_no_fields_for_private_values_or_commands(self):
        for key in ('stderr','stdout','argv','command','path','failure','parameters','pid','grants'):
            value=row();value[key]='FAKE_PRIVATE_TOKEN_SOURCE_TEXT'
            with self.assertRaises(ValueError):self.native.validate(value,capture.MANIFEST)

    def test_bool_nonfinite_timing_and_identity_reject(self):
        for key,value in [('frame',True),('frame_count',float('nan')),('target_index',0),('manifest_sha256','b'*64),('accepted',True)]:
            with self.assertRaises(ValueError):self.native.validate({**row(),key:value},capture.MANIFEST)

    def test_native_retention_and_safe_v2_projection(self):
        helper=capture.CaptureSafeReader();helper._cleanups=[]
        try:
            helper.setUp();helper.put(row());helper.retain();value=helper.observe()
            self.assertTrue(safe.is_safe_capture_observation(value))
            self.assertEqual(value['schema'],'bie.task036.m1.capture-controller-observation/2')
            self.assertEqual(value['guard_code'],'COMPLETION_COUNTS');self.assertFalse(value['render_passed'])
        finally:helper.doCleanups()

    def test_old_raw_reader_statuses_stay_distinct(self):
        before=safe.empty('quantitative','standard',48,192)
        self.assertEqual(before['process']['receipt_state'],safe.UNKNOWN)
        self.assertEqual(before['resource']['receipt_state'],safe.UNKNOWN)
        self.assertFalse(before['render_passed'])

    def test_unknown_or_malformed_v2_stays_invalid_not_pass(self):
        value=safe.empty_capture();value.update(schema='bie.task036.m1.capture-controller-observation/2',receipt_state='VALID')
        self.assertFalse(safe.is_safe_capture_observation(value))

    def test_missing_extra_bool_negative_or_overflow_calls_rejected(self):
        for calls in (None,{}, {'private':'SOURCE'}, {**row()['policy_calls'],'create':True},
            {**row()['policy_calls'],'completion':-1},{**row()['policy_calls'],'stitcher':3}):
            with self.assertRaises(ValueError):self.native.validate({**row(),'policy_calls':calls},capture.MANIFEST)

    def test_attempted_rejected_callback_is_not_reported_zero(self):
        value=observed("try{mediaPolicyPhase('MEDIA_CALLBACK_PRE',()=>{throw new Error()})}catch(_){}console.log(JSON.stringify(policyCalls));")
        self.assertEqual(value['pre_stitcher'],1);self.assertEqual(value['stitcher'],0)

    def test_counter_cannot_report_other_phase_as_attempted(self):
        value=row('MEDIA_CALLBACK_PRE','ARGUMENT_SHAPE');value['policy_calls']['pre_stitcher']=0
        with self.assertRaises(ValueError):self.native.validate(value,capture.MANIFEST)


class PolicyGuardDelegation(unittest.TestCase):
    def test_success_delegates_once_returns_identical_object(self):
        value=observed("const object={},result=mediaPolicyPhase('MEDIA_POLICY_COMPLETE',()=>object);console.log(JSON.stringify({identity:result===object,phase:observation.phase,schema:observation.schema}));")
        self.assertEqual(value,{'identity':True,'phase':'RENDER_MEDIA','schema':'bie.capture-controller-failure/1'})

    def test_exception_identity_and_fixed_guard_preserved(self):
        value=observed("const e=new Error('FAKE_PRIVATE_TOKEN');Object.defineProperty(e,'m1_media_guard',{value:'COMPLETION_COUNTS'});let calls=0,same=false;try{mediaPolicyPhase('MEDIA_POLICY_COMPLETE',()=>{calls++;throw e})}catch(x){same=x===e}console.log(JSON.stringify({calls,same,observation}));")
        self.assertTrue(value['same']);self.assertEqual(value['calls'],1)
        self.assertEqual(value['observation']['guard_code'],'COMPLETION_COUNTS');self.assertNotIn('FAKE_PRIVATE',json.dumps(value))

    def test_unknown_library_exception_not_inspected(self):
        value=observed("const e=new Error();Object.defineProperty(e,'message',{get(){throw new Error('SENSITIVE_GETTER')}});let same=false;try{mediaPolicyPhase('MEDIA_POLICY_COMPLETE',()=>{throw e})}catch(x){same=x===e}console.log(JSON.stringify({same,guard:observation.guard_code}));")
        self.assertEqual(value,{'same':True,'guard':'NONE_RECORDED'})

    def test_accessor_guard_not_executed(self):
        value=observed("let reads=0;const e=new Error();Object.defineProperty(e,'m1_media_guard',{get(){reads++;return 'COMPLETION_COUNTS'}});try{mediaPolicyPhase('MEDIA_POLICY_COMPLETE',()=>{throw e})}catch(_){}console.log(JSON.stringify({reads,guard:observation.guard_code}));")
        self.assertEqual(value,{'reads':0,'guard':'NONE_RECORDED'})

    def test_unknown_or_object_guard_is_not_serialized(self):
        for text in ('"FAKE_PRIVATE_TOKEN"','{secret:"FAKE_PRIVATE_TOKEN"}'):
            value=observed("const e=new Error();Object.defineProperty(e,'m1_media_guard',{value:"+text+"});try{mediaPolicyPhase('MEDIA_POLICY_COMPLETE',()=>{throw e})}catch(_){}console.log(JSON.stringify(observation));")
            self.assertEqual(value['guard_code'],'NONE_RECORDED');self.assertNotIn('FAKE_PRIVATE',json.dumps(value))

    def test_observer_failure_cannot_replace_original(self):
        value=observed("const util=require('node:util'),original=util.types.isNativeError,e=new Error();let same=false;try{util.types.isNativeError=()=>{throw new Error('OBSERVER_FAILURE')};try{mediaPolicyPhase('MEDIA_POLICY_COMPLETE',()=>{throw e})}catch(x){same=x===e}}finally{util.types.isNativeError=original}console.log(JSON.stringify({same,restored:util.types.isNativeError===original}));")
        self.assertEqual(value,{'same':True,'restored':True})

    def test_pre_mark_failure_still_delegates_once(self):
        value=observed("mark=()=>{throw new Error('PRIVATE_OBSERVER_FAULT')};let calls=0;const object={},result=mediaPolicyPhase('MEDIA_POLICY_COMPLETE',()=>{calls++;return object});console.log(JSON.stringify({calls,same:result===object}));")
        self.assertEqual(value,{'calls':1,'same':True})

    def test_post_mark_failure_preserves_successful_return(self):
        value=observed("const original=mark;let marks=0,calls=0;mark=p=>{if(++marks===2)throw new Error('PRIVATE_OBSERVER_FAULT');original(p)};const object={},result=mediaPolicyPhase('MEDIA_POLICY_COMPLETE',()=>{calls++;return object});console.log(JSON.stringify({calls,same:result===object,marks}));")
        self.assertEqual(value,{'calls':1,'same':True,'marks':2})

    def test_schema_write_failure_preserves_exception_identity(self):
        value=observed("Object.defineProperty(observation,'schema',{set(){throw new Error('PRIVATE_OBSERVER_FAULT')}});let calls=0,same=false;const error=new Error('PRIVATE_DELEGATE_FAULT');try{mediaPolicyPhase('MEDIA_POLICY_COMPLETE',()=>{calls++;throw error})}catch(e){same=e===error}console.log(JSON.stringify({calls,same}));")
        self.assertEqual(value,{'calls':1,'same':True})

    def test_counter_write_failure_preserves_successful_return(self):
        value=observed("Object.defineProperty(policyCalls,'completion',{get(){throw new Error('PRIVATE_OBSERVER_FAULT')}});let calls=0;const object={},result=mediaPolicyPhase('MEDIA_POLICY_COMPLETE',()=>{calls++;return object});console.log(JSON.stringify({calls,same:result===object}));")
        self.assertEqual(value,{'calls':1,'same':True})

    def test_actual_controller_completion_rejection_recorded_and_browser_closed(self):
        helper=threads.MediaControllerDispatch();helper._cleanups=[]
        try:
            code,out=helper.execute(missing_callback=True)
            self.assertEqual(code,2);self.assertFalse((out/'RESULT.json').exists())
            value=json.loads((out/'CAPTURE_PROCESS_DIAGNOSTIC.json').read_text())
            self.assertEqual(value['schema'],'bie.capture-controller-failure/2')
            self.assertEqual((value['phase'],value['guard_code']),('MEDIA_POLICY_COMPLETE','COMPLETION_COUNTS'))
            self.assertEqual((out/'closed.txt').read_text(),'closed')
        finally:helper.doCleanups()

    def test_actual_controller_policy_rejection_has_no_fallback(self):
        helper=threads.MediaControllerDispatch();helper._cleanups=[]
        try:
            code,out=helper.execute(policy={**threads.POLICY,'schema':'unknown'})
            self.assertEqual(code,2);self.assertFalse((out/'RESULT.json').exists())
            value=json.loads((out/'CAPTURE_PROCESS_DIAGNOSTIC.json').read_text())
            self.assertEqual((value['phase'],value['guard_code']),('MEDIA_POLICY_CREATE','POLICY_IDENTITY'))
            self.assertEqual((out/'closed.txt').read_text(),'closed')
        finally:helper.doCleanups()

    def test_helper_success_arguments_byte_values_unchanged(self):
        before=ROOT/'docs/productization/task036-media-policy-observation-amendment/bounded_media_threads.cjs.before'
        value=threads.run_node('const old=require('+json.dumps(str(before))+');console.log(JSON.stringify({pre:JSON.stringify(old.lowerArguments("pre-stitcher",pre))===JSON.stringify(api.lowerArguments("pre-stitcher",pre)),stitch:JSON.stringify(old.lowerArguments("stitcher",stitch))===JSON.stringify(api.lowerArguments("stitcher",stitch))}));')
        self.assertEqual(value,{'pre':True,'stitch':True})

    def test_helper_error_class_message_and_fixed_category(self):
        value=threads.run_node('let a;try{api.lowerArguments("unknown",pre)}catch(e){a={error:e instanceof Error,message:e.message,code:e.m1_media_guard,enumerable:Object.keys(e)}}console.log(JSON.stringify(a));')
        self.assertEqual(value,{'error':True,'message':'M1_MEDIA_THREAD_POLICY_REJECTED','code':'CALLBACK_KIND','enumerable':[]})


class PolicyObservationAmendment(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from scripts import compiler_media_policy_observation_amendment as module
        cls.amendment=module;cls.doc=module.validate(ROOT)
        tmp=tempfile.TemporaryDirectory();cls.addClassCleanup(tmp.cleanup);cls.root=Path(tmp.name)
        shutil.copytree(ROOT/'docs/productization',cls.root/'docs/productization',ignore=shutil.ignore_patterns('*.zip'))
        shutil.copytree(ROOT/'scripts',cls.root/'scripts',ignore=shutil.ignore_patterns('__pycache__'))
        (cls.root/'manifests').mkdir()
        shutil.copyfile(ROOT/'manifests/post_dir_integration_004.json',cls.root/'manifests/post_dir_integration_004.json')
        for path in ('bie/compiler/real_paint.py','bie/compiler/qa_support/remotion_raster_capture.cjs','bie/compiler/qa_support/bounded_media_threads.cjs'):
            target=cls.root/path;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/path,target)

    def test_exact_git_preimages_and_chain(self):
        from scripts import compiler_media_thread_amendment as prior
        self.assertEqual(self.amendment.validate(self.root),self.doc);prior.validate(self.root)
        for row in self.doc['replacements']:
            old=subprocess.check_output(['git','show','2e08e31b1f16d044af3204d0e12afab5362a9765:'+row['path']],cwd=ROOT)
            self.assertEqual(old,(self.root/row['preimage']).read_bytes())
            self.assertEqual(sha256(old).hexdigest(),row['original_sha256'])

    def test_every_active_or_preimage_tamper_rejects(self):
        for row in self.doc['replacements']:
            for field in ('path','preimage'):
                path=self.root/row[field];before=path.read_bytes()
                try:
                    path.write_bytes(before+b'UNAUTHORIZED')
                    with self.assertRaises(ValueError):self.amendment.validate(self.root)
                finally:path.write_bytes(before)

    def test_recomputed_manifest_extra_or_duplicate_not_blessed(self):
        path=self.root/self.amendment.DOCUMENT;before=path.read_bytes()
        try:
            for variant in ('duplicate','extra','bless'):
                doc=deepcopy(self.doc)
                if variant=='bless':doc['replacements'][0]['active_sha256']='f'*64
                else:
                    item=deepcopy(doc['replacements'][0])
                    if variant=='extra':item['path']='bie/compiler/unapproved.py'
                    doc['replacements'].append(item)
                path.write_text(json.dumps(doc))
                with self.assertRaises(ValueError):self.amendment.validate(self.root)
        finally:path.write_bytes(before)

    def test_prior_sealed_thread_manifest_cannot_change(self):
        path=self.root/self.amendment.PREVIOUS_DOCUMENT;before=path.read_bytes()
        try:
            path.write_bytes(before+b' ')
            with self.assertRaises(ValueError):self.amendment.validate(self.root)
        finally:path.write_bytes(before)

    def test_unlisted_or_wrong_parent_source_rejected(self):
        for path in ('bie/compiler/unapproved.py','bie/compiler/real_paint.py'):
            with self.assertRaises(ValueError):self.amendment.authenticated_previous_bytes(self.root,path,'a'*64)

    def test_all_worker_security_and_validation_call_asts_unchanged(self):
        path='bie/compiler/real_paint.py';before=ast.parse((ROOT/self.doc['replacements'][2]['preimage']).read_text())
        after=ast.parse((ROOT/path).read_text())
        for name in ('run_chromium_isolated','isolated_typecheck','WorkerPolicy','inspect_owner_fit','inspect_paint_quality','inspect_counterfactual_capture'):
            def calls(tree):return [ast.dump(n,include_attributes=False) for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id==name]
            self.assertEqual(calls(before),calls(after),name)

    def test_new_file_once_no_native_or_safety_overlap(self):
        from tests.compiler import run_m1_tests as runner
        lanes,inherited=runner.inventory();path='tests/compiler/test_m1_media_policy_observation.py'
        self.assertEqual(lanes['new'].count(path),1);self.assertEqual(len(lanes['native-extra']),214)
        self.assertNotIn(path,lanes['native-extra']);self.assertNotIn(path,lanes['safety']);self.assertNotIn(path,inherited)


if __name__=='__main__':unittest.main()
