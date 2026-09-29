from ani_helpers import *
import json,subprocess,sys
from pathlib import Path
from bie.qa.animation_v2.bridge import prepare_release_evidence
from bie.qa.animation_v2.codec import load_request,load_policy
from bie.qa.release_v2.evaluator import ReleaseEvaluator
from bie.qa.release_v2.contracts import EvidenceBundle
from test_capture import synthetic_capture
from jsonschema import Draft202012Validator
ROOT=Path(__file__).resolve().parents[2]

class BridgeTests(FixtureCase):
    def prepare(self,r=None,p=None,c=None,**opts):
        r=self.r if r is None else r;p=self.p if p is None else p;c=self.c if c is None else c
        return prepare_release_evidence(r,c,self.root,p,as_of=NOW,**options(r,p,**opts))
    def test_healthy_gate_not_run(self):self.assertEqual(self.prepare().envelope.status,'NOT_RUN')
    def test_unsigned_evidence_only(self):
        e=self.prepare().envelope;self.assertEqual(e.signer_key_id,'UNSIGNED');self.assertEqual(e.signature,'')
    def test_bad_animation_fails_gate(self):
        r=change_track(self.r,keyframes=(Keyframe(0,40000),Keyframe(100,200000)));self.assertEqual(self.prepare(r).envelope.status,'FAIL')
    def test_missing_semantic_review_not_run(self):self.assertEqual(self.prepare(reviews=()).envelope.status,'NOT_RUN')
    def test_report_payload_not_product_acceptance(self):
        d=json.loads(self.prepare().report_bytes);self.assertFalse(d['product_accepted']);self.assertFalse(d['actual_media_evaluated'])
    def test_report_hash_and_size(self):
        x=self.prepare();self.assertEqual(x.envelope.report.sha256,hashlib.sha256(x.report_bytes).hexdigest());self.assertEqual(x.envelope.report.size,len(x.report_bytes))
    def test_no_output_written_by_preparation(self):
        self.prepare();self.assertFalse((self.root/'qa_animation_reports').exists())
    def test_real_release_evaluator_stays_blocked(self):
        x=self.prepare();f=self.root/x.envelope.report.path;f.parent.mkdir(parents=True);f.write_bytes(x.report_bytes)
        result=ReleaseEvaluator().evaluate(EvidenceBundle('2.0.0',self.c,(x.envelope,)),self.root,as_of=NOW)
        self.assertEqual(result.release_status,'BLOCKED');self.assertFalse(result.product_accepted)
    def test_wrong_candidate(self):
        with self.assertRaises(ContractError):self.prepare(c=replace(self.c,candidate_id='different'))
    def test_wrong_run(self):
        r=replace(self.r,source=replace(self.r.source,run_id='other'))
        with self.assertRaises(ContractError):self.prepare(r)
    def test_wrong_revision(self):
        r=replace(self.r,source=replace(self.r.source,revision='1'*40))
        with self.assertRaises(ContractError):self.prepare(r)
    def test_capture_must_be_in_candidate(self):
        capture=synthetic_capture(self.root,self.r,self.p);r=replace(self.r,captures=(capture,))
        with self.assertRaises(ContractError):self.prepare(r)
    def test_capture_candidate_binding_avoids_hash_cycle(self):
        cp=synthetic_capture(self.root,self.r,self.p);c=replace(self.c,artifacts=self.c.artifacts+(cp.html,cp.observations)+cp.screenshots)
        r=replace(self.r,captures=(cp,),source=replace(self.r.source,candidate_digest=c.content_digest))
        e=self.prepare(r,c=c);self.assertEqual(e.envelope.status,'NOT_RUN');self.assertNotIn('ANI_CAPTURE_CONTEXT',{x['code'] for x in json.loads(e.report_bytes)['declared_animation_plan']['temporal']['findings']})
    def test_extra_candidate_source_rejected(self):
        extra=artifact(self.root,'extra.txt',b'extra','extra-source','source');c=replace(self.c,artifacts=self.c.artifacts+(extra,));r=replace(self.r,source=replace(self.r.source,candidate_digest=c.content_digest))
        with self.assertRaises(ContractError):self.prepare(r,c=c)
    def test_report_id_collision(self):
        extra=artifact(self.root,'reserved.txt',b'extra','qa16-animation-quality-report');c=replace(self.c,artifacts=self.c.artifacts+(extra,));r=replace(self.r,source=replace(self.r.source,candidate_digest=c.content_digest))
        with self.assertRaises(ContractError):self.prepare(r,c=c)

class CLIAndSchemaTests(FixtureCase):
    def run_cli(self,*,bad_request=False,output=None):
        a=self.root/'request.json';b=self.root/'policy.json';a.write_bytes(b'{}' if bad_request else canonical_bytes(asdict(self.r)));b.write_bytes(canonical_bytes(asdict(self.p)))
        cmd=[sys.executable,'-B','-m','bie.qa.animation_v2','--request',str(a),'--policy',str(b),'--artifact-root',str(self.root),'--as-of',str(NOW)]
        if output:cmd+=['--output',str(output)]
        return subprocess.run(cmd,cwd=ROOT,capture_output=True,timeout=20)
    def test_unsigned_cli_review(self):
        r=self.run_cli();self.assertEqual(r.returncode,3,r.stderr);self.assertEqual(json.loads(r.stdout)['status'],'REVIEW_REQUIRED')
    def test_invalid_cli_input(self):self.assertEqual(self.run_cli(bad_request=True).returncode,4)
    def test_cli_real_byte_error_blocked(self):
        (self.root/self.r.source.sources[0].artifact.path).write_bytes(b'bad');self.assertEqual(self.run_cli().returncode,2)
    def test_cli_refuses_overwrite(self):
        f=self.root/'output.json';f.write_bytes(b'preserve');r=self.run_cli(output=f);self.assertEqual(r.returncode,4);self.assertEqual(f.read_bytes(),b'preserve')
    def test_cli_output_exclusive_create(self):
        f=self.root/'new-result.json';self.assertEqual(self.run_cli(output=f).returncode,3);self.assertEqual(json.loads(f.read_bytes())['status'],'REVIEW_REQUIRED')
    def test_structural_schemas_valid(self):
        for name,value in [('request',self.r),('policy',self.p),('review',signed_reviews(self.r,self.p)[0])]:
            with self.subTest(schema=name):
                schema=json.loads((ROOT/f'docs/qa_section16/batch009/{name}.schema.json').read_text());Draft202012Validator.check_schema(schema);Draft202012Validator(schema).validate(json.loads(canonical_bytes(asdict(value))))
    def test_schema_closed_fields(self):
        schema=json.loads((ROOT/'docs/qa_section16/batch009/request.schema.json').read_text());d=json.loads(canonical_bytes(asdict(self.r)));d['product_accepted']=True;self.assertTrue(list(Draft202012Validator(schema).iter_errors(d)))
    def test_schema_rejects_float_time(self):
        schema=json.loads((ROOT/'docs/qa_section16/batch009/request.schema.json').read_text());d=json.loads(canonical_bytes(asdict(self.r)));d['tracks'][0]['keyframes'][0]['time_ms']=0.1;self.assertTrue(list(Draft202012Validator(schema).iter_errors(d)))
    def test_schema_not_cross_reference_authority(self):
        d=json.loads(canonical_bytes(asdict(self.p)));d['timing_rules'][0]['left_track_id']='missing'
        schema=json.loads((ROOT/'docs/qa_section16/batch009/policy.schema.json').read_text());Draft202012Validator(schema).validate(d)
        with self.assertRaises(ContractError):load_policy(canonical_bytes(d))

class InvariantIntegrationTests(FixtureCase):
    def conserving(self):
        a=Track('amount-a','standard','marker','value_milli','amount-a','explain',(Keyframe(0,0),Keyframe(2000,1000)))
        obj=replace(self.r.objects[0],object_id='second',semantic_id='second-meaning')
        b=replace(a,track_id='amount-b',object_id='second',semantic_id='amount-b',keyframes=(Keyframe(0,1000),Keyframe(2000,0)))
        specs=tuple(TrackRequirement(t.track_id,t.mode_id,t.object_id,t.property,t.semantic_id,t.purpose,('ani-claim',),True,0,1000,'any') for t in (a,b))
        inv=Invariant('conservation','standard','sum_constant',('amount-a','amount-b'),0,2000,1000)
        r=replace(self.r,objects=self.r.objects+(obj,),tracks=self.r.tracks+(a,b));p=replace(self.p,objects=r.objects,tracks=self.p.tracks+specs,invariants=(inv,));return r,p
    def test_conserved_quantity(self):
        r,p=self.conserving();self.assertEqual(self.check(r,p).status,'CHECKS_PASSED')
    def test_conserved_endpoints_not_enough(self):
        r,p=self.conserving();r=change_track(r,'amount-a',keyframes=(Keyframe(0,0),Keyframe(1000,900),Keyframe(2000,1000)));self.assertCode(self.check(r,p),'ANI_SEMANTIC_INVARIANT')
    def test_unknown_curve_never_invariant_proof(self):
        r,p=self.conserving();r=change_track(r,'amount-a',interpolation='spring');self.assertCode(self.check(r,p),'ANI_UNSUPPORTED_INTERPOLATION');self.assertEqual(self.check(r,p).status,'REVIEW_REQUIRED')
    def test_invariant_missing_member(self):
        r,p=self.conserving();r=replace(r,tracks=r.tracks[:-1]);self.assertCode(self.check(r,p),'ANI_INVARIANT_MISSING_TRACK')
    def test_invariant_cannot_shrink_window(self):
        r,p=self.conserving();r=change_track(r,'amount-a',keyframes=(Keyframe(100,0),Keyframe(2000,1000)));self.assertCode(self.check(r,p),'ANI_INVARIANT_COVERAGE')
    def test_split_property_jump(self):
        x=self.r.tracks[0];a=replace(x,keyframes=(Keyframe(0,40000),Keyframe(1000,100000)));b=replace(x,track_id='move-later',keyframes=(Keyframe(1500,150000),Keyframe(2000,200000)))
        r=replace(self.r,tracks=(a,)+self.r.tracks[1:]+(b,));s=replace(self.p.tracks[0],endpoints_required=False);p=replace(self.p,tracks=(s,)+self.p.tracks[1:]+(replace(s,track_id='move-later'),));self.assertCode(self.check(r,p),'ANI_UNDECLARED_PROPERTY_JUMP')
