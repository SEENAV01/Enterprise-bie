from h4_support import *
import json,sys,subprocess
from bie.qa.domain_quality_v2.parser import ParserPolicy,evaluate_parser
from jsonschema import Draft202012Validator,ValidationError
ROOT=Path(__file__).resolve().parents[2]
class InterfaceChecks(TempCase):
    def test_native_float_fingerprint_exact(self):self.assertNotEqual(native_digest(0.1),native_digest(0.10000000000000002))
    def test_native_float_type_preserved(self):self.assertNotEqual(native_digest(1.0),native_digest(1))
    def test_native_tag_collision_prevented(self):self.assertNotEqual(native_digest(1.0),native_digest(['float_hex',(1.0).hex()]))
    def test_native_key_order_stable(self):self.assertEqual(native_digest({'b':1.0,'a':2}),native_digest({'a':2,'b':1.0}))
    def test_native_nonfinite_rejected(self):
        with self.assertRaises(ContractError):native_digest(float('nan'))
    def test_native_infinity_rejected(self):
        with self.assertRaises(ContractError):native_digest(float('inf'))
    def test_native_unsupported_rejected(self):
        with self.assertRaises(ContractError):native_digest({1,2})
    def test_native_tree_budget(self):
        v=1
        for _ in range(35):v=[v]
        with self.assertRaises(ContractError):native_digest(v)
    def parser_fixture(self):
        p=ParserPolicy(('expr',));b=binding(p);d=payload('BIE-QA-HARD-015',b,expressions=[dict(case_id='expr',text='x*y+z')]);ref=save(self.root,'parser.json',d)
        return p,b,d,ref
    def test_parser_byte_bound_api(self):
        p,b,d,ref=self.parser_fixture();r,details=evaluate_parser(ref,self.root,b,p);self.assertEqual(r.status,'REVIEW_REQUIRED');self.assertFalse(details['expr']['native_mismatch'])
    def test_parser_missing_requirement(self):
        p,b,d,ref=self.parser_fixture();d['expressions'][0]['case_id']='wrong'
        with self.assertRaises(ContractError):evaluate_parser(save(self.root,'parser.json',d),self.root,b,p)
    def test_parser_source_tamper(self):
        p,b,d,ref=self.parser_fixture();(self.root/'parser.json').write_text('{}')
        with self.assertRaises(ContractError):evaluate_parser(ref,self.root,b,p)
    def test_tolerance_owned_by_operator(self):
        p=MathPolicy(('u',));b=binding(p);c=dict(case_id='u',kind='units',value='1',from_unit='m',to_unit='m',result='1.0000001',absolute_tolerance='0.000001')
        with self.assertRaises(ContractError):evaluate_math(save(self.root,'m.json',payload('BIE-QA-HARD-014',b,cases=[c])),self.root,b,p)
    def test_explicit_tolerance_supported(self):
        p=MathPolicy(('u',),max_absolute_tolerance='0.000001');b=binding(p);c=dict(case_id='u',kind='units',value='1',from_unit='m',to_unit='m',result='1.0000001',absolute_tolerance='0.000001')
        r,_=evaluate_math(save(self.root,'m.json',payload('BIE-QA-HARD-014',b,cases=[c])),self.root,b,p);self.assertEqual(r.status,'REVIEW_REQUIRED')
    def test_read_only_cli(self):
        p,b,d,ref=self.parser_fixture();req=self.root/'request.json';req.write_bytes(canonical_bytes(dict(binding=asdict(b),artifact=asdict(ref),policy=asdict(p))))
        before={x.name:x.read_bytes()for x in self.root.iterdir()}
        x=subprocess.run([sys.executable,'-B','-m','bie.qa.domain_quality_v2','parser','--root',str(self.root),'--request',str(req)],cwd=ROOT,capture_output=True,timeout=20)
        self.assertEqual(x.returncode,3,x.stderr);self.assertEqual(json.loads(x.stdout)['report']['status'],'REVIEW_REQUIRED');self.assertEqual(before,{x.name:x.read_bytes()for x in self.root.iterdir()})
    def test_cli_unknown_callback_rejected(self):
        p,b,d,ref=self.parser_fixture();req=self.root/'request.json';req.write_bytes(canonical_bytes(dict(binding=asdict(b),artifact=asdict(ref),policy=asdict(p),callback='os.system')))
        x=subprocess.run([sys.executable,'-B','-m','bie.qa.domain_quality_v2','parser','--root',str(self.root),'--request',str(req)],cwd=ROOT,capture_output=True,timeout=20);self.assertEqual(x.returncode,2)
    def test_visual_request_observation_type(self):
        p,b,n,h,s,o,png=visual_fixture(self.root);o['blocked_requests']='none'
        with self.assertRaises(ContractError):evaluate_visual(n,h,s,self.root,b,p,capture=(o,png))
    def test_visual_boolean_markup_rejected(self):
        p,b,n,h,s,o,png=visual_fixture(self.root);o['unsupported_markup']=True
        with self.assertRaises(ContractError):evaluate_visual(n,h,s,self.root,b,p,capture=(o,png))
    def test_visual_empty_nonstring_text_rejected(self):
        p,b,n,h,s,o,png=visual_fixture(self.root);o['nodes'][0]['text']=0
        with self.assertRaises(ContractError):evaluate_visual(n,h,s,self.root,b,p,capture=(o,png))

def make_doc(root,k):
    if k==12:return reason_fixture(root)[-1]
    if k==13:return pedagogy_fixture(root)[-1]
    if k==14:
        p=MathPolicy(('a',));return payload('BIE-QA-HARD-014',binding(p),cases=[{'case_id':'a','kind':'derivative','expression':'x','variable':'x','result':'1'}])
    if k==15:
        p=ParserPolicy(('a',));return payload('BIE-QA-HARD-015',binding(p),expressions=[{'case_id':'a','text':'x*y+z'}])
    if k==16:return director_fixture(root)[-1]
    if k==17:return visual_fixture(root)[-2]
    p=ParserPolicy(('a',));return dict(binding=asdict(binding(p)),artifact=asdict(save(root,'a',b'x')),policy=asdict(p))
for k in range(12,19):
    name=f'HARD_{k:03d}_'+('CAPTURE'if k==17 else'INPUT') if k<18 else'READ_ONLY_REQUEST'
    def good(self,k=k,name=name):
        s=json.loads((ROOT/'schemas/qa/section16_h4'/f'{name}.schema.json').read_text());Draft202012Validator.check_schema(s);Draft202012Validator(s).validate(json.loads(json.dumps(make_doc(self.root,k))))
    def extra(self,k=k,name=name):
        s=json.loads((ROOT/'schemas/qa/section16_h4'/f'{name}.schema.json').read_text());d=json.loads(json.dumps(make_doc(self.root,k)));d['release_authorized']=True
        with self.assertRaises(ValidationError):Draft202012Validator(s).validate(d)
    def missing(self,k=k,name=name):
        s=json.loads((ROOT/'schemas/qa/section16_h4'/f'{name}.schema.json').read_text());d=json.loads(json.dumps(make_doc(self.root,k)));d.pop(s['required'][0])
        with self.assertRaises(ValidationError):Draft202012Validator(s).validate(d)
    setattr(InterfaceChecks,'test_schema_positive_'+str(k),good);setattr(InterfaceChecks,'test_schema_extra_'+str(k),extra);setattr(InterfaceChecks,'test_schema_missing_'+str(k),missing)
