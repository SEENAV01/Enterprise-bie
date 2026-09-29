from dataclasses import replace
import json, os, random, subprocess, sys
from pathlib import Path
from source_helpers import *
from bie.qa.source_v2.bridge import prepare_release_evidence
from bie.qa.source_v2.evaluator import _covered_nonspace
from bie.qa.release_v2.contracts import EvidenceBundle
from bie.qa.release_v2.evaluator import ReleaseEvaluator

ROOT=Path(__file__).resolve().parents[2]

class BridgeTests(FixtureCase):
    def prepared(self,request=None,candidate=None):
        return prepare_release_evidence(self.request if request is None else request,
             self.candidate if candidate is None else candidate,self.root,self.policy,as_of=NOW)
    def materialize(self,items):
        for item in items:
            path=self.root/item.envelope.report.path;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(item.report_bytes)
    def test_two_unsigned_source_gate_envelopes(self):
        items=self.prepared();self.assertEqual(len(items),2)
        by={x.envelope.gate_id:x.envelope for x in items}
        self.assertEqual(by['source_grounding'].status,'NOT_RUN')
        self.assertEqual(by['citation_provenance'].status,'PASS')
        self.assertTrue(all(x.envelope.signature=='' and x.envelope.signer_key_id=='UNSIGNED' for x in items))
    def test_release_v2_consumer_accepts_shape_but_blocks_unsigned_release(self):
        items=self.prepared();self.materialize(items)
        bundle=EvidenceBundle('2.0.0',self.candidate,tuple(i.envelope for i in items))
        report=ReleaseEvaluator().evaluate(bundle,self.root,as_of=NOW)
        self.assertEqual(report.release_status,'BLOCKED');self.assertFalse(report.product_accepted)
        self.assertFalse(report.release_authorized)
        self.assertIn('source_grounding',report.blocking_gates)
    def test_report_bytes_hash_matches_envelope(self):
        for item in self.prepared():
            self.assertEqual(hashlib.sha256(item.report_bytes).hexdigest(),item.envelope.report.sha256)
            self.assertEqual(len(item.report_bytes),item.envelope.report.size)
    def test_bridge_is_read_only(self):
        before=sorted(p.relative_to(self.root).as_posix() for p in self.root.rglob('*'))
        self.prepared()
        self.assertEqual(before,sorted(p.relative_to(self.root).as_posix() for p in self.root.rglob('*')))
    def test_changed_candidate_cannot_reuse_request(self):
        with self.assertRaises(ContractError):self.prepared(candidate=replace(self.candidate,candidate_id='new'))
    def test_run_mismatch_cannot_reuse_request(self):
        with self.assertRaises(ContractError):self.prepared(request=replace(self.request,run_id='new'))
    def test_request_ref_must_match_actual_candidate_inventory(self):
        o=replace(self.request.outputs[0],artifact=replace(self.request.outputs[0].artifact,path='another.txt'))
        with self.assertRaises(ContractError):self.prepared(request=replace(self.request,outputs=(o,)))
    def test_missing_candidate_source_coverage_rejected(self):
        other=artifact(self.root,'inputs/other.txt',b'Another source','other-source','source')
        candidate=replace(self.candidate,artifacts=self.candidate.artifacts+(other,))
        request=replace(self.request,candidate_digest=candidate.content_digest)
        with self.assertRaises(ContractError):self.prepared(request,candidate)
    def test_bridge_recomputes_after_artifact_tampering(self):
        self.prepared();(self.root/'inputs/source.txt').write_text(TEXT.replace('5','9'))
        items=self.prepared()
        self.assertTrue(all(x.envelope.status=='FAIL' for x in items))
    def test_no_verified_artifacts_cannot_issue_evidence(self):
        (self.root/'inputs/source.txt').unlink();(self.root/'surfaces/narration.txt').unlink()
        with self.assertRaises(ContractError):self.prepared()
    def test_tampered_bridge_report_rejected_by_release_byte_check(self):
        items=self.prepared();self.materialize(items)
        path=self.root/items[0].envelope.report.path;path.write_bytes(b'FORGED')
        r=ReleaseEvaluator().evaluate(EvidenceBundle('2.0.0',self.candidate,tuple(i.envelope for i in items)),self.root,as_of=NOW)
        self.assertEqual(r.release_status,'BLOCKED')
        self.assertTrue(any(c.status!='PASS' for c in r.artifact_checks))

class CliTests(FixtureCase):
    def call(self,payload=None,expected='narration'):
        request_path=self.root/'request.json'
        request_path.write_bytes(canonical_bytes(self.request.to_dict()) if payload is None else payload)
        return subprocess.run([sys.executable,'-B','-m','bie.qa.source_v2','--request',str(request_path),
            '--root',str(self.root),'--expected-output',expected,'--as-of',str(NOW)],cwd=ROOT,
            env={**os.environ,'PYTHONPATH':str(ROOT),'PYTHONDONTWRITEBYTECODE':'1'},text=True,capture_output=True,timeout=15)
    def test_default_cli_does_not_claim_contextual_support(self):
        result=self.call();self.assertEqual(result.returncode,2,result.stderr)
        d=json.loads(result.stdout);self.assertEqual(d['grounding']['status'],'REVIEW_REQUIRED')
        self.assertEqual(d['provenance']['status'],'CHECKS_PASSED')
    def test_cli_invalid_contract_exit(self):
        result=self.call(b'{}');self.assertEqual(result.returncode,3)
        self.assertFalse(json.loads(result.stdout)['product_accepted'])
    def test_cli_operator_scope_mismatch_blocks(self):
        result=self.call(expected='missing');self.assertEqual(result.returncode,2)
        self.assertEqual(json.loads(result.stdout)['provenance']['status'],'BLOCKED')
    def test_cli_exact_replay_bytes(self):
        self.assertEqual(self.call().stdout,self.call().stdout)

class PropertyTests(FixtureCase):
    def test_seeded_unicode_source_and_tamper_cases(self):
        rng=random.Random(16002)
        tokens=('प्रकाश','त्रिभुज','Δ','木','café','e\u0301','5','3.14','lamp','test','العلم')
        # 64 valid/invalid paired cases within ONE unittest, not 128 tests.
        for i in range(64):
            value=' '.join(rng.choice(tokens) for _ in range(rng.randrange(1,9)))+'.'
            with self.subTest(case=i):
                request,_,policy=fixture(self.root,value)
                result=self.check(request,policy)
                self.assertEqual(result.provenance.status,'CHECKS_PASSED')
                c=replace(request.citations[0],quote=value+'x')
                result=self.check(replace(request,citations=(c,)),policy)
                self.assertEqual(result.provenance.status,'BLOCKED')
    def test_interval_union_matches_independent_character_oracle(self):
        rng=random.Random(16003)
        for i in range(200):
            value=' a b  c.\nΔ  e\u0301 木 '
            spans=[]
            for _ in range(rng.randrange(0,20)):
                a=rng.randrange(len(value));b=rng.randrange(a+1,len(value)+1);spans.append((a,b))
            expected=sum(not ch.isspace() and any(a<=j<b for a,b in spans) for j,ch in enumerate(value))
            with self.subTest(case=i):self.assertEqual(_covered_nonspace(value,spans),expected)
    def test_any_receipt_byte_tamper_fails_authentication(self):
        a=signed(self.request,self.policy);k=key();v=AssessmentVerifier((k,))
        for i in range(64):
            sig=a.signature[:i]+('0' if a.signature[i]!='0' else '1')+a.signature[i+1:]
            with self.subTest(position=i):self.assertFalse(v.verify(replace(a,signature=sig),self.request,self.policy,NOW).authenticated)
