from vis_helpers import *
import json,subprocess,sys
from bie.qa.visual_v2.codec import load_request,load_policy,request_from_dict,policy_from_dict,load_reviews
from bie.qa.visual_v2.capture import measurement_from_browser

class ContractsCodec(FixtureCase):
    def test_request_json_roundtrip(self):self.assertEqual(load_request(canonical_bytes(asdict(self.request))),self.request)
    def test_policy_json_roundtrip(self):self.assertEqual(load_policy(canonical_bytes(asdict(self.policy))),self.policy)
    def test_reviews_json_roundtrip(self):
        rr=signed_reviews(self.request,self.policy);self.assertEqual(load_reviews(canonical_bytes([asdict(r) for r in rr])),rr)
    def test_unknown_json_field_rejected(self):
        d=asdict(self.request);d['accepted']=True
        with self.assertRaises(ContractError):load_request(canonical_bytes(d))
    def test_missing_json_field_rejected(self):
        d=asdict(self.request);del d['captures']
        with self.assertRaises(ContractError):load_request(canonical_bytes(d))
    def test_duplicate_json_keys_rejected(self):
        with self.assertRaises(ContractError):load_request(b'{"a":1,"a":2}')
    def test_nonfinite_json_rejected(self):
        with self.assertRaises(ContractError):load_request(b'{"x":NaN}')
    def test_bool_not_integer_json(self):
        d=json.loads(canonical_bytes(asdict(self.request)));d['states'][0]['start_ms']=False
        with self.assertRaises(ContractError):request_from_dict(d)
    def test_float_not_integer_json(self):
        d=json.loads(canonical_bytes(asdict(self.request)));d['states'][0]['start_ms']=0.0
        with self.assertRaises(ContractError):request_from_dict(d)
    def test_nested_extra_field_rejected(self):
        d=json.loads(canonical_bytes(asdict(self.request)));d['states'][0]['measurements'][0]['box']['z']=0
        with self.assertRaises(ContractError):request_from_dict(d)
    def test_empty_request_inventory(self):
        with self.assertRaises(ContractError):replace(self.request,elements=())
    def test_duplicate_elements(self):
        with self.assertRaises(ContractError):replace(self.request,elements=self.request.elements+(self.request.elements[0],))
    def test_mutable_list_not_tuple(self):
        with self.assertRaises(ContractError):replace(self.request,states=list(self.request.states))
    def test_policy_unknown_view(self):
        with self.assertRaises(ContractError):replace(self.policy,states=(replace(self.policy.states[0],view_id='unknown'),))
    def test_policy_unknown_object(self):
        with self.assertRaises(ContractError):replace(self.policy,states=(replace(self.policy.states[0],object_ids=('unknown',)),))
    def test_policy_overlapping_state_windows(self):
        with self.assertRaises(ContractError):replace(self.policy,states=self.policy.states+(replace(self.policy.states[0],state_id='duplicate-time'),))
    def test_reserved_review_scope_id(self):
        with self.assertRaises(ContractError):replace(self.request,states=(replace(self.request.states[0],state_id='visual-scope'),))
    def test_relation_target_alias(self):
        with self.assertRaises(ContractError):replace(self.request,relations=(replace(self.request.relations[0],relation_id='object-1'),))
    def test_budget_limits_total_capture_bytes(self):
        r,c=fake_capture(self.root,self.request,self.policy)
        big=replace(c.html,size=65*1024*1024)
        with self.assertRaises(ContractError):replace(r,captures=(replace(c,html=big),))
    def test_native_dependency_exact_bytes(self):
        root=Path(__file__).resolve().parents[2];entries=json.loads((root/'evidence/qa_section16/native_dependencies_008.json').read_text())
        self.assertEqual(len(entries),2)
        for e in entries:
            with self.subTest(path=e['path']):
                b=(root/e['path']).read_bytes();self.assertEqual(hashlib.sha256(b).hexdigest(),e['sha256']);self.assertEqual(len(b),e['bytes'])
                self.assertEqual(hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest(),e['git_blob_sha'])
    def test_schema_matches_structural_request_and_policy(self):
        import jsonschema
        root=Path(__file__).resolve().parents[2]
        for name,obj in [('request',self.request),('policy',self.policy)]:
            with self.subTest(schema=name):
                schema=json.loads((root/f'docs/qa_section16/batch008/{name}.schema.json').read_text())
                jsonschema.Draft202012Validator.check_schema(schema);jsonschema.validate(json.loads(canonical_bytes(asdict(obj))),schema)
    def test_cli_unsigned_and_exclusive_output(self):
        root=Path(__file__).resolve().parents[2];a=self.root/'request.json';b=self.root/'policy.json';out=self.root/'result.json'
        a.write_bytes(canonical_bytes(asdict(self.request)));b.write_bytes(canonical_bytes(asdict(self.policy)))
        args=[sys.executable,'-B','-m','bie.qa.visual_v2','--request',str(a),'--policy',str(b),'--artifact-root',str(self.root),'--as-of',str(NOW),'--output',str(out)]
        proc=subprocess.run(args,cwd=root,capture_output=True,text=True,timeout=15)
        self.assertEqual(proc.returncode,3,proc.stderr);self.assertEqual(json.loads(out.read_bytes())['status'],'REVIEW_REQUIRED')
        proc2=subprocess.run(args,cwd=root,capture_output=True,text=True,timeout=15);self.assertEqual(proc2.returncode,4)

# Boundary cases reject invalid values rather than silently coerce them.
INVALID_CONSTRUCTORS={
 'rect_boolean':lambda:Rect(True,0,1,1),'rect_float':lambda:Rect(0.5,0,1,1),'rect_zero_width':lambda:Rect(0,0,0,1),
 'rect_negative_height':lambda:Rect(0,0,1,-1),'rect_unbounded':lambda:Rect(10**12,0,1,1),
 'color_overflow':lambda:RGBA(256,0,0),'color_bool':lambda:RGBA(True,0,0),'color_negative':lambda:RGBA(-1,0,0),
 'view_zero':lambda:ViewRequirement('bad',0,450,Rect(0,0,1,1)),
 'view_pixels':lambda:ViewRequirement('bad',4096,4096,Rect(0,0,1,1)),
 'view_safe_outside':lambda:ViewRequirement('bad',100,100,Rect(0,0,101000,100000)),
 'view_caption_outside':lambda:ViewRequirement('bad',100,100,Rect(0,0,100000,100000),(Rect(0,0,101000,100000),)),
 'min_font_boolean':lambda:VisualLimits(min_font_mpx=True),'contrast_impossible':lambda:VisualLimits(min_contrast_ppm=22000000),
 'opacity_overflow':lambda:VisualLimits(min_opacity_ppm=1000001),'empty_encoding':lambda:VisualElement('e','s','text',('c',),'m',()),
 'unknown_role':lambda:VisualElement('e','s','banana',('c',),'m'),
 'self_relation':lambda:VisualRelation('r','s','above','a','a',('c',)),
 'same_time':lambda:VisualState('s','scene','view',0,0,()),
 'bad_mode':lambda:VisualState('s','scene','view',0,10,(),'full-video-proven'),
}
for name,constructor in INVALID_CONSTRUCTORS.items():
 def test(self,constructor=constructor):
    with self.assertRaises(ContractError):constructor()
 setattr(ContractsCodec,'test_invalid_'+name,test)
