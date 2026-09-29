from video_helpers import *
from bie.qa.video_v2.bridge import prepare_release_evidence
from bie.qa.video_v2.adapters import from_native_render
from bie.qa.release_v2.evaluator import ReleaseEvaluator

class BridgeTests(FixtureCase):
    def prepare(self,r=None,c=None):
        r=self.r if r is None else r;c=self.c if c is None else c
        v,k=signed(r,self.p)
        with patch('bie.qa.video_v2.evaluator.inspect_bytes',return_value=self.obs):return prepare_release_evidence(r,c,self.root,self.p,as_of=NOW,reviews=v,verifier=k)
    def test_no_complete_gate_pass(self):self.assertEqual([x.envelope.status for x in self.prepare()],['NOT_RUN']*3)
    def test_three_gate_names(self):self.assertEqual({x.envelope.gate_id for x in self.prepare()},{'code_compile','video_render','rendered_frame_inspection'})
    def test_unsigned(self):self.assertTrue(all(x.envelope.signature=='' and x.envelope.signer_key_id=='UNSIGNED' for x in self.prepare()))
    def test_bytes_match_report_hash(self):
        for x in self.prepare():self.assertEqual(hashlib.sha256(x.report_bytes).hexdigest(),x.envelope.report.sha256)
    def test_candidate_mismatch(self):self.assertRaises(ContractError,self.prepare,c=replace(self.c,candidate_id='wrong'))
    def test_wrong_candidate_artifact(self):self.assertRaises(ContractError,self.prepare,r=replace(self.r,video=replace(self.movie,sha256='f'*64)))
    def test_bridge_does_not_write(self):self.prepare();self.assertFalse((self.root/'qa_video_reports').exists())
    def test_release_evaluator_blocks(self):
        xs=self.prepare()
        for x in xs:p=self.root/x.envelope.report.path;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(x.report_bytes)
        e=EvidenceBundle('2.0.0',self.c,tuple(x.envelope for x in xs));r=ReleaseEvaluator().evaluate(e,self.root,as_of=NOW);self.assertEqual(r.release_status,'BLOCKED');self.assertFalse(r.product_accepted)
    def test_tampered_media_marks_fail(self):(self.root/'movie.mp4').write_bytes(b'tampered');self.assertTrue(all(x.envelope.status=='FAIL' for x in self.prepare()))

class NativeAdapterTests(FixtureCase):
    def raw(self):return dict(schema_version='native-fixture',run_id='run',mode='full',composition_id='lesson',passed=True,failure_code=None,errors=[],output_path=self.movie.path,expected_frames=8,media=dict(width=32,height=24,fps=4.0,duration_s=2.0),input_sha256='1'*64,recipe_sha256='2'*64,evidence_directory='evidence',execution_kind='native',process_started=True,artifact_sha256=self.movie.sha256,artifact_size_bytes=self.movie.size,accepted=False)
    def adapt(self,r=None):return from_native_render(self.raw() if r is None else r,self.movie,run_id='run',composition_id='lesson')
    def test_native_stays_unverified(self):r=self.adapt();self.assertFalse(r['execution_authenticated']);self.assertFalse(r['actual_media_redecoded']);self.assertFalse(r['product_accepted'])
    def test_native_smoke_preserved(self):r=self.raw();r['mode']='smoke';self.assertTrue(self.adapt(r)['requires_full_render'])
    def test_native_acceptance_rejected(self):r=self.raw();r['accepted']=True;self.assertRaises(ContractError,self.adapt,r)
    def test_native_media_mismatch(self):r=self.raw();r['artifact_sha256']='0'*64;self.assertRaises(ContractError,self.adapt,r)
    def test_native_failed_flags(self):r=self.raw();r['process_started']=False;self.assertRaises(ContractError,self.adapt,r)
    def test_native_other_run(self):r=self.raw();r['run_id']='other';self.assertRaises(ContractError,self.adapt,r)
    def test_native_extra_field(self):r=self.raw();r['certified']=True;self.assertRaises(ContractError,self.adapt,r)
    def test_native_nonfinite(self):r=self.raw();r['media']['fps']=float('nan');self.assertRaises(ContractError,self.adapt,r)

class SchemaTests(FixtureCase):
    def test_structural_schemas(self):
        from jsonschema import Draft202012Validator
        for name,obj in [('request',self.r),('policy',self.p),('execution_receipt',self.cr),('review',signed(self.r,self.p)[0][0])]:
            with self.subTest(schema=name):
                schema=json.loads((ROOT/f'docs/qa_section16/batch011/{name}.schema.json').read_bytes());Draft202012Validator.check_schema(schema);Draft202012Validator(schema).validate(json.loads(canonical_bytes(asdict(obj))))
