from repair_helpers import *
from bie.qa.repair_v2.bridge import prepare_release_evidence
from bie.qa.repair_v2.__main__ import main
from bie.qa.repair_v2.adapters import inspect_audio_invalidation
from bie.qa.repair_v2.worker import validate_registry,validator_digest
from bie.qa.release_v2.evaluator import ReleaseEvaluator
import contextlib,io

class BridgeCli(Fixture):
    def staged(self):
        r=self.run_proposal();s=load_snapshot(canonical_bytes(r['candidate']));c=ReleaseCandidate('2.0.0','candidate-new',s.run_id,s.revision,s.artifacts);return r,c
    def test_bridge_never_passes(self):r,c=self.staged();x=prepare_release_evidence(r,c,r['staged_directory'],as_of=NOW);self.assertEqual(x.envelope.status,'NOT_RUN');self.assertEqual(x.envelope.signature,'')
    def test_bridge_actual_bytes(self):
        r,c=self.staged();(Path(r['staged_directory'])/'generated/lesson.txt').write_bytes(b'bad');self.assertRaises(ContractError,prepare_release_evidence,r,c,r['staged_directory'],as_of=NOW)
    def test_bridge_candidate_binding(self):r,c=self.staged();self.assertRaises(ContractError,prepare_release_evidence,r,replace(c,run_id='wrong'),r['staged_directory'],as_of=NOW)
    def test_bridge_receipt_tamper(self):r,c=self.staged();r['product_accepted']=True;self.assertRaises(ContractError,prepare_release_evidence,r,c,r['staged_directory'],as_of=NOW)
    def test_existing_release_evaluator_blocks(self):
        r,c=self.staged();root=Path(r['staged_directory']);x=prepare_release_evidence(r,c,root,as_of=NOW);p=root/x.envelope.report.path;p.parent.mkdir(parents=True);p.write_bytes(x.report_bytes)
        v=ReleaseEvaluator().evaluate(EvidenceBundle('2.0.0',c,(x.envelope,)),root,as_of=NOW);self.assertEqual(v.release_status,'BLOCKED');self.assertFalse(v.product_accepted)
    def test_bridge_not_write_reports(self):r,c=self.staged();prepare_release_evidence(r,c,r['staged_directory'],as_of=NOW);self.assertFalse((Path(r['staged_directory'])/'qa_repair_reports').exists())
    def test_bridge_json_roundtrip(self):r,c=self.staged();r=json.loads(canonical_bytes(r));self.assertEqual(prepare_release_evidence(r,c,r['staged_directory'],as_of=NOW).envelope.status,'NOT_RUN')
    def test_unsigned_cli(self):self.assertEqual(self.cli(),3)
    def test_cli_no_overwrite(self):p=self.home/'result.json';p.write_bytes(b'original');self.assertEqual(self.cli(str(p)),4);self.assertEqual(p.read_bytes(),b'original')
    def test_cli_writes_new(self):p=self.home/'result.json';self.assertEqual(self.cli(str(p)),3);self.assertFalse(json.loads(p.read_bytes())['code_execution_enabled'])
    def test_cli_detects_tamper(self):(self.root/'generated/lesson.txt').write_bytes(b'2+9');self.assertEqual(self.cli(),2)
    def cli(self,out=None):
        for n,o in [('snapshot',self.snapshot),('batch',self.batch),('policy',self.policy)]: (self.home/(n+'.json')).write_bytes(canonical_bytes(asdict(o)))
        args=['--snapshot',str(self.home/'snapshot.json'),'--batch',str(self.home/'batch.json'),'--policy',str(self.home/'policy.json'),'--artifact-root',str(self.root),'--as-of',str(NOW)]
        if out:args+=['--output',out]
        with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):return main(args)
    def test_unapproved_check_implementation_rejected(self):self.assertRaises(ContractError,validate_registry,self.policy,('numeric',),{'numeric':wrong_binding})
    def test_builtin_not_valid_validator(self):self.assertRaises(ContractError,validator_digest,len)
    def test_no_embedded_eval_callable(self):self.assertRaises(ContractError,validator_digest,object())
    def native(self):return dict(schema_version='bie.audio.repair-invalidation/1',product_accepted=False,repository_mutated=False,invalidations=[dict(task_id=k,new_status='INVALIDATED') for k in ('AUDIO_TTS_CACHE','AUDIO_SYNC','AUDIO_MIX','CAPTIONS','ANIMATION_CLOCKS','AUDIO_QA','COMP_NARRATION_PLAN','COMP_GENERATED_SOURCE','RENDER')])
    def test_native_adapter_not_dispatch(self):d=inspect_audio_invalidation(self.native());self.assertFalse(d['dispatch_performed']);self.assertFalse(d['canonical_status_updated'])
    def test_native_adapter_no_provenance_promotion(self):d=inspect_audio_invalidation(self.native());self.assertFalse(d['artifact_bytes_verified']);self.assertTrue(d['requires_actual_downstream_rerun'])
    def test_native_missing_downstream_rejected(self):d=self.native();d['invalidations'].pop();self.assertRaises(ContractError,inspect_audio_invalidation,d)
    def test_native_claimed_acceptance_rejected(self):d=self.native();d['product_accepted']=True;self.assertRaises(ContractError,inspect_audio_invalidation,d)
    def test_native_status_not_reused(self):d=self.native();d['invalidations'][0]['new_status']='PASS';self.assertRaises(ContractError,inspect_audio_invalidation,d)
    def test_six_structural_schemas(self):
        from jsonschema import Draft202012Validator
        objects={'snapshot':self.snapshot,'failure_batch':self.batch,'policy':self.policy,'proposal':self.proposal(),'check_outcome':numeric_check(self.root,self.snapshot,self.policy),'review':self.inv()[0]}
        for name,obj in objects.items():
            with self.subTest(schema=name):
                schema=json.loads((ROOT/f'docs/qa_section16/batch013/{name}.schema.json').read_bytes());Draft202012Validator.check_schema(schema);Draft202012Validator(schema).validate(json.loads(canonical_bytes(asdict(obj))))
