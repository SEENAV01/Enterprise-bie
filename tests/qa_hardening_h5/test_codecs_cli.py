from h5_helpers import *
from bie.qa.media_runtime_v2.codec import *
from bie.qa.media_runtime_v2.motion import *
import jsonschema
class Codecs(Case):
    def test_stream_roundtrip(self):
        p=StreamPolicy(64,48,'12',12);self.assertEqual(load_policy('stream',canonical_bytes(asdict(p))),p)
    def test_motion_roundtrip(self):
        p=MotionPolicy(2,'1',(Track('m','x',('0','1','2','3'),'0','3','10'),),('x',));self.assertEqual(load_policy('motion',canonical_bytes(asdict(p))),p)
    def test_speech_roundtrip(self):
        p=SpeechPolicy('hi','voice',(('term',('a','b')),));self.assertEqual(load_policy('speech',canonical_bytes(asdict(p))),p)
    def test_unknown_policy_field(self):
        d=asdict(StreamPolicy(64,48,'12',12));d['skip_checks']=True
        with self.assertRaisesRegex(ContractError,'H5_CODEC_FIELDS'):load_policy('stream',canonical_bytes(d))
    def test_duplicate_json_key(self):
        with self.assertRaises(ContractError):load_policy('stream',b'{"width":64,"width":72}')
    def test_float_is_not_frame_clock(self):
        with self.assertRaises(ContractError):load_policy('stream',b'{"width":64,"height":48,"fps":29.97,"frames":1}')
    def test_unknown_policy_kind(self):
        with self.assertRaisesRegex(ContractError,'H5_CODEC_KIND'):load_policy('arbitrary-execute',b'{}')
    def test_request_cannot_choose_tools(self):
        p=StreamPolicy(64,48,'12',12);a=ref(self.root,'a',b'1','a',True);d={'binding':asdict(bind(p)),'artifact':asdict(a),'tools':{}}
        with self.assertRaisesRegex(ContractError,'H5_REQUEST_FIELDS'):load_request(canonical_bytes(d),'stream')
    def test_seven_schemas(self):
        files=tuple((ROOT/'hardening/section16_h5/schemas').glob('*.json'));self.assertEqual(len(files),7)
        for f in files:jsonschema.Draft202012Validator.check_schema(json.loads(f.read_text()))
    def test_schema_rejects_extra_fields(self):
        schema=json.loads((ROOT/'hardening/section16_h5/schemas/stream.schema.json').read_text());v=asdict(StreamPolicy(64,48,'12',12));v=json.loads(canonical_bytes(v));jsonschema.validate(v,schema);v['passed']=True
        with self.assertRaises(jsonschema.ValidationError):jsonschema.validate(v,schema)
    def test_schema_rejects_bool_width(self):
        schema=json.loads((ROOT/'hardening/section16_h5/schemas/stream.schema.json').read_text());v=json.loads(canonical_bytes(asdict(StreamPolicy(64,48,'12',12))));v['width']=True
        with self.assertRaises(jsonschema.ValidationError):jsonschema.validate(v,schema)
class CLI(Case):
    def seed(self):
        p=MotionPolicy(2,'1',(Track('m','x',('0','1','2','3'),'0','3','10'),),('distance',));b=bind(p)
        rs=[dict(frame=i,timestamp=str(i),mode='standard',meaning_ids=['distance'],values={'m.x':str(i*3)},binding=asdict(b)) for i in range(2)]
        a=ref(self.root,'trace',b''.join(canonical_bytes(x)+b'\n' for x in rs),'trace',True)
        (self.root/'policy.json').write_bytes(canonical_bytes(asdict(p)));(self.root/'request.json').write_bytes(canonical_bytes({'binding':asdict(b),'artifact':asdict(a)}))
    def run_cli(self,*extra):
        return subprocess.run([sys.executable,'-B','-m','bie.qa.media_runtime_v2','motion','--root',str(self.root),'--policy',str(self.root/'policy.json'),'--request',str(self.root/'request.json'),*extra],cwd=ROOT,capture_output=True,timeout=15)
    def test_healthy_unsigned_cli_review_exit(self):self.seed();p=self.run_cli();self.assertEqual(p.returncode,3,p.stderr);self.assertEqual(json.loads(p.stdout)['report']['status'],'REVIEW_REQUIRED')
    def test_existing_report_is_preserved(self):
        self.seed();f=self.root/'out.json';f.write_bytes(b'ORIGINAL');p=self.run_cli('--output',str(f));self.assertEqual(p.returncode,4);self.assertEqual(f.read_bytes(),b'ORIGINAL')
    def test_bad_request_is_json_error(self):
        self.seed();(self.root/'request.json').write_text('{}');p=self.run_cli();self.assertEqual(p.returncode,4);self.assertEqual(json.loads(p.stderr)['status'],'BLOCKED')
