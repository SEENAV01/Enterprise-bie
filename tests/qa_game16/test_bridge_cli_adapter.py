from game_helpers import *
from bie.qa.game_v2.bridge import prepare_release_evidence
from bie.qa.game_v2.adapters import inspect_native_browser
from bie.qa.release_v2.evaluator import ReleaseEvaluator
from bie.qa.game_v2.__main__ import main
from unittest.mock import patch
import contextlib

class BridgeTests(FixtureCase):
    def prepare(self,r=None,c=None):
        r=r or self.r;c=c or self.c;return prepare_release_evidence(r,c,self.root,self.p,as_of=NOW,**options(r,self.p))
    def test_four_gates(self):self.assertEqual({x.envelope.gate_id for x in self.prepare()},{'game_build','game_runtime','game_interactions','game_learning_alignment'})
    def test_no_full_gate_pass(self):self.assertEqual([x.envelope.status for x in self.prepare()],['NOT_RUN']*4)
    def test_unsigned(self):self.assertTrue(all(x.envelope.signature=='' and x.envelope.signer_key_id=='UNSIGNED' for x in self.prepare()))
    def test_report_hash(self):
        for x in self.prepare():self.assertEqual(hashlib.sha256(x.report_bytes).hexdigest(),x.envelope.report.sha256)
    def test_candidate_binding(self):self.assertRaises(ContractError,self.prepare,c=replace(self.c,candidate_id='wrong'))
    def test_artifact_binding(self):self.assertRaises(ContractError,self.prepare,r=replace(self.r,outputs=(replace(self.r.outputs[0],sha256='0'*64),)+self.r.outputs[1:]))
    def test_no_writes(self):self.prepare();self.assertFalse((self.root/'qa_game_reports').exists())
    def test_broken_output_fail(self):(self.root/self.r.outputs[0].path).write_bytes(b'bad');self.assertTrue(all(x.envelope.status=='FAIL' for x in self.prepare()))
    def test_full_release_stays_blocked(self):
        xs=self.prepare()
        for x in xs:p=self.root/x.envelope.report.path;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(x.report_bytes)
        r=ReleaseEvaluator().evaluate(EvidenceBundle('2.0.0',self.c,tuple(x.envelope for x in xs)),self.root,as_of=NOW);self.assertEqual(r.release_status,'BLOCKED');self.assertFalse(r.product_accepted)
    def test_missing_screenshot_candidate(self):
        c=replace(self.c,artifacts=tuple(a for a in self.c.artifacts if a.artifact_id!='screen-pointer-0-0'));r=replace(self.r,candidate_digest=c.content_digest,source=replace(self.r.source,candidate_digest=c.content_digest));self.assertRaises(ContractError,self.prepare,r,c)

class AdapterTests(FixtureCase):
    def native(self):return dict(target='about:blank',execution_mode='playwright_devtools_self_contained_bundle',browser_version='SYNTHETIC',studio_grade=True,slide_deck=False,entity_count=2,external_requests=[],console_errors=[],page_errors=[],runtime_binding_keys=['value'],bundle_sha256=self.r.outputs[1].sha256,product_accepted=False,sandbox_uid=65534,sandbox_no_new_privs=True,renderer_seccomp=True,canonical_worker_blob='f'*40)
    def adapt(self,d=None):return inspect_native_browser(d or self.native(),self.r.outputs[1])
    def test_about_blank_not_promoted(self):self.assertTrue(self.adapt()['requires_entrypoint_capture'])
    def test_no_actual_byte_claim(self):self.assertFalse(self.adapt()['artifact_bytes_verified'])
    def test_no_execution_auth_claim(self):self.assertFalse(self.adapt()['execution_authenticated'])
    def test_no_quality_claim(self):self.assertFalse(self.adapt()['native_game_acceptance']);self.assertFalse(self.adapt()['product_accepted'])
    def test_no_internal_dispatch_acceptance(self):self.assertTrue(self.adapt()['requires_independent_ui_oracle'])
    def test_acceptance_rejected(self):d=self.native();d['product_accepted']=True;self.assertRaises(ContractError,self.adapt,d)
    def test_hash_rejected(self):d=self.native();d['bundle_sha256']='0'*64;self.assertRaises(ContractError,self.adapt,d)
    def test_fields_rejected(self):d=self.native();d['certified']=True;self.assertRaises(ContractError,self.adapt,d)
    def test_boolean_rejected(self):d=self.native();d['studio_grade']=1;self.assertRaises(ContractError,self.adapt,d)
    def test_array_rejected(self):d=self.native();d['external_requests']='not array';self.assertRaises(ContractError,self.adapt,d)
    def test_failed_native_not_concealed(self):d=self.native();d['page_errors']=['error'];self.assertTrue(self.adapt(d)['reported_errors'])

class SchemaCliTests(FixtureCase):
    def test_all_structural_schemas(self):
        from jsonschema import Draft202012Validator
        for name,obj in [('request',self.r),('policy',self.p),('build_receipt',load_build((self.root/self.r.build_receipt.path).read_bytes())),('runtime_receipt',load_runtime((self.root/self.r.runtime_receipt.path).read_bytes())),('review',signed_reviews(self.r,self.p)[0])]:
            with self.subTest(schema=name):
                schema=json.loads((ROOT/f'docs/qa_section16/batch012/{name}.schema.json').read_bytes());Draft202012Validator.check_schema(schema);Draft202012Validator(schema).validate(json.loads(canonical_bytes(asdict(obj))))
    def cli(self,extra=()):
        (self.root/'request.json').write_bytes(canonical_bytes(asdict(self.r)));(self.root/'policy.json').write_bytes(canonical_bytes(asdict(self.p)))
        args=['game-qa','--request',str(self.root/'request.json'),'--policy',str(self.root/'policy.json'),'--artifact-root',str(self.root),'--as-of',str(NOW),*extra]
        with patch('sys.argv',args),contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):return main()
    def test_cli_unsigned_review(self):self.assertEqual(self.cli(),3)
    def test_cli_broken_artifact_blocked(self):(self.root/self.r.outputs[0].path).write_bytes(b'wrong');self.assertEqual(self.cli(),2)
    def test_cli_write_new(self):self.assertEqual(self.cli(('--output',str(self.root/'new.json'))),3);self.assertTrue((self.root/'new.json').exists())
    def test_cli_no_overwrite(self):p=self.root/'new.json';p.write_bytes(b'original');self.assertEqual(self.cli(('--output',str(p))),4);self.assertEqual(p.read_bytes(),b'original')
