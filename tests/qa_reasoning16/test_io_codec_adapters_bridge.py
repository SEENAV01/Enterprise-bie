from dataclasses import replace,asdict
from pathlib import Path
import os,json,subprocess,sys,hashlib
from re_helpers import *
from bie.qa.reasoning_v2.codec import load_request,load_policy,load_reviews
from bie.qa.reasoning_v2.adapters import import_prerequisite_graph,inspect_legacy_decisions,exact_ppm
from bie.qa.reasoning_v2.bridge import prepare_release_evidence
from bie.qa.release_v2.contracts import EvidenceBundle
from bie.qa.release_v2.evaluator import ReleaseEvaluator
from bie.prerequisite_intelligence.graph import build_graph,Edge
from bie.reasoning.decision_contracts import ReasoningDecision,EvidenceRef
ROOT=Path(__file__).resolve().parents[2]

class CodecIoTests(FixtureCase):
    def test_reviews_roundtrip(self):
        rs=signed_reviews(self.request,self.policy);self.assertEqual(load_reviews(canonical_bytes([asdict(x) for x in rs])),rs)
    def test_embedded_trust_rejected(self):
        d=self.request.to_dict();d['trusted']=True
        with self.assertRaises(ContractError):load_request(canonical_bytes(d))
    def test_nested_override_rejected(self):
        d=self.request.to_dict();d['steps'][0]['override']=True
        with self.assertRaises(ContractError):load_request(canonical_bytes(d))
    def test_duplicate_json_keys(self):
        with self.assertRaises(ContractError):load_request(b'{"schema_version":"1.0.0","schema_version":"1.0.0"}')
    def test_float_json_rejected(self):
        raw=json.dumps(self.request.to_dict()).replace('"confidence_ppm": 950000','"confidence_ppm": 950000.0').encode()
        with self.assertRaises(ContractError):load_request(raw)
    def test_null_collection_rejected(self):
        d=self.request.to_dict();d['events']=None
        with self.assertRaises(ContractError):load_request(canonical_bytes(d))
    def test_malformed_json_unicode_and_nonfinite(self):
        for raw in (b'{',b'not json',b'\xff',b'NaN',b'Infinity'):
            with self.subTest(raw=raw),self.assertRaises(ContractError):load_request(raw)
    def test_unsafe_path_rejected(self):
        d=self.request.to_dict();d['calibrations'][0]['artifact']['path']='../outside.json'
        with self.assertRaises(ContractError):load_request(canonical_bytes(d))
    def test_source_bytes_tampered(self):
        path=self.root/self.request.source.sources[0].artifact.path;path.write_bytes(path.read_bytes().replace(b'switch',b'sw1tch'))
        result=self.run_check();self.assertNotEqual(result.status,'CHECKS_PASSED');self.assertIn('ARTIFACT_HASH_MISMATCH',codes(result.source.provenance))
    def test_calibration_bytes_tampered(self):
        path=self.root/self.request.calibrations[0].artifact.path;path.write_bytes(path.read_bytes().replace(b'950000',b'940000'))
        self.assertCode(self.run_check(),'uncertainty','ARTIFACT_HASH_MISMATCH')
    def test_missing_calibration_file(self):
        (self.root/self.request.calibrations[0].artifact.path).unlink();self.assertCode(self.run_check(),'uncertainty','ARTIFACT_OPEN_OR_READ_FAILED')
    def test_calibration_symlink_rejected(self):
        path=self.root/self.request.calibrations[0].artifact.path;copy=path.with_name('copy.json');copy.write_bytes(path.read_bytes());path.unlink();path.symlink_to(copy)
        self.assertCode(self.run_check(),'uncertainty','ARTIFACT_OPEN_OR_READ_FAILED')
    def test_calibration_hardlink_rejected(self):
        path=self.root/self.request.calibrations[0].artifact.path;os.link(path,path.with_name('hard.json'));self.assertCode(self.run_check(),'uncertainty','HARD_LINK_REJECTED')
    def test_edited_result_rejected(self):
        result=self.run_check();edited=replace(result,proof_witnesses=())
        with self.assertRaises(ContractError):verify_reports(edited,self.request,self.root,self.policy,as_of=NOW,**options(self.request,self.policy))
    def test_exact_result_recomputed(self):
        result=self.run_check();self.assertEqual(verify_reports(result,self.request,self.root,self.policy,as_of=NOW,**options(self.request,self.policy)),result)
    def cli(self,output=None):
        req=self.root/'request.json';pol=self.root/'policy.json';req.write_bytes(canonical_bytes(self.request.to_dict()));pol.write_bytes(canonical_bytes(self.policy.to_dict()))
        args=[sys.executable,'-B','-m','bie.qa.reasoning_v2','--request',str(req),'--policy',str(pol),'--artifact-root',str(self.root),'--as-of',str(NOW)]
        if output:args+=['--output',str(output)]
        return subprocess.run(args,cwd=ROOT,capture_output=True,timeout=15)
    def test_unsigned_cli_blocked(self):
        run=self.cli();self.assertEqual(run.returncode,2);self.assertEqual(json.loads(run.stdout)['status'],'BLOCKED')
    def test_cli_output_does_not_overwrite(self):
        path=self.root/'existing.json';path.write_text('DO NOT OVERWRITE');run=self.cli(path);self.assertEqual(run.returncode,4);self.assertEqual(path.read_text(),'DO NOT OVERWRITE')
    def test_cli_invalid_contract_exit(self):
        p=self.root/'bad.json';p.write_text('{}')
        run=subprocess.run([sys.executable,'-B','-m','bie.qa.reasoning_v2','--request',str(p),'--policy',str(p),'--artifact-root',str(self.root),'--as-of',str(NOW)],cwd=ROOT,capture_output=True,timeout=15)
        self.assertEqual(run.returncode,4);self.assertIn(b'REASONING_FIELDS_MISMATCH',run.stderr)

class AdapterTests(FixtureCase):
    def test_real_pr_graph_import(self):
        nodes,rules=import_prerequisite_graph(build_graph(('a','b'),(Edge('a','b'),)));self.assertEqual(nodes,('a','b'));self.assertEqual(rules[0].prerequisite,'a')
    def test_asymmetric_pr_graph_rejected(self):
        graph=build_graph(('a','b'),(Edge('a','b'),));graph.incoming['b']=set()
        with self.assertRaises(ContractError):import_prerequisite_graph(graph)
    def test_malformed_pr_node_inventory(self):
        graph=build_graph(('a','b'),(Edge('a','b'),));graph.nodes.add('x')
        with self.assertRaises(ContractError):import_prerequisite_graph(graph)
    def test_fake_graph_type_rejected(self):
        with self.assertRaises(ContractError):import_prerequisite_graph({'a':['b']})
    def legacy(self):return ReasoningDecision('decision','causal_explanation','lamp','Why on?','on','Toy circuit supports this inference.',0.95,evidence_refs=[EvidenceRef('source-file','primary',0.9)])
    def test_real_reasoning_contract_inspected_without_trust_upgrade(self):
        result=inspect_legacy_decisions((self.legacy(),))[0];self.assertEqual(result.confidence_ppm,950000);self.assertFalse(result.trusted_evidence_available);self.assertFalse(result.normalized_proof_available)
    def test_invalid_legacy_dependency(self):
        with self.assertRaises(ContractError):inspect_legacy_decisions((replace(self.legacy(),depends_on_decisions=['missing']),))
    def test_boolean_legacy_confidence(self):
        with self.assertRaises(ContractError):inspect_legacy_decisions((replace(self.legacy(),confidence=True),))
    def test_nonfinite_legacy_strength(self):
        with self.assertRaises(ContractError):inspect_legacy_decisions((replace(self.legacy(),evidence_refs=[EvidenceRef('source-file','primary',float('nan'))]),))
    def test_lossy_ppm_conversion_rejected(self):
        with self.assertRaises(ContractError):exact_ppm(0.1234567)
    def test_legacy_review_flag_preserved(self):self.assertTrue(inspect_legacy_decisions((replace(self.legacy(),requires_review=True),))[0].requires_review)

class BridgeTests(FixtureCase):
    def prepare(self,request=None,candidate=None,**kw):
        r=request or self.request;return prepare_release_evidence(r,candidate or self.candidate,self.root,self.policy,as_of=NOW,**options(r,self.policy,**kw))
    def test_text_success_still_not_run_for_full_media_gate(self):
        prepared=self.prepare();self.assertEqual(len(prepared),2);self.assertTrue(all(x.envelope.status=='NOT_RUN' for x in prepared))
    def test_bridge_unsigned(self):self.assertTrue(all(x.envelope.signature=='' and x.envelope.signer_key_id=='UNSIGNED' for x in self.prepare()))
    def test_bridge_report_bytes_verified(self):
        for p in self.prepare():self.assertEqual(hashlib.sha256(p.report_bytes).hexdigest(),p.envelope.report.sha256)
    def test_candidate_identity_mismatch(self):
        with self.assertRaises(ContractError):self.prepare(candidate=replace(self.candidate,run_id='other'))
    def test_candidate_artifact_content_mismatch(self):
        ref=replace(self.candidate.artifacts[-1],sha256='0'*64);candidate=replace(self.candidate,artifacts=self.candidate.artifacts[:-1]+(ref,));r=replace(self.request,source=replace(self.request.source,candidate_digest=candidate.content_digest))
        with self.assertRaises(ContractError):self.prepare(r,candidate)
    def test_failed_prerequisite_exports_failure(self):
        r=replace(self.request,events=(replace(self.request.events[0],position=3),self.request.events[1]));self.assertEqual(self.prepare(r)[0].envelope.status,'FAIL')
    def test_full_release_remains_blocked(self):
        prepared=self.prepare()
        for p in prepared:
            f=self.root/p.envelope.report.path;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(p.report_bytes)
        bundle=EvidenceBundle('2.0.0',self.candidate,tuple(x.envelope for x in prepared))
        result=ReleaseEvaluator().evaluate(bundle,self.root,as_of=NOW)
        self.assertEqual(result.release_status,'BLOCKED');self.assertFalse(result.product_accepted)
