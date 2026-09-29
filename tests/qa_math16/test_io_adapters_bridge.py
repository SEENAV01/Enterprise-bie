from math_helpers import *
import os,subprocess,sys
from bie.qa.math_v2.codec import load_request,load_policy,load_reviews
from bie.qa.math_v2.adapters import import_node,import_equation,export_dimension,inspect_native_chain,inspect_native_numeric
from bie.qa.math_v2.bridge import prepare_release_evidence
from bie.qa.release_v2.contracts import EvidenceBundle
from bie.qa.release_v2.evaluator import ReleaseEvaluator
from bie.math_intelligence.expression_ast import Node,parse_expression
from bie.math_intelligence.equation_ast import parse_equation,Equation as NativeEquation
from bie.math_intelligence.derivation_chain import Step as NativeStep
ROOT=Path(__file__).resolve().parents[2]

class CodecTests(FixtureCase):
    def test_request_roundtrip(self):self.assertEqual(load_request(canonical_bytes(self.request.to_dict())),self.request)
    def test_policy_roundtrip(self):self.assertEqual(load_policy(canonical_bytes(asdict(self.policy))),self.policy)
    def test_reviews_roundtrip(self):
        r=signed_reviews(self.request,self.policy);self.assertEqual(load_reviews(canonical_bytes([asdict(x) for x in r])),r)
    def test_trust_injection(self):
        d=self.request.to_dict();d['trusted']=True
        with self.assertRaises(ContractError):load_request(canonical_bytes(d))
    def test_unknown_nested_field(self):
        d=self.request.to_dict();d['formulas'][0]['equation']['release_override']=True
        with self.assertRaises(ContractError):load_request(canonical_bytes(d))
    def test_null_array(self):
        d=self.request.to_dict();d['numericals']=None
        with self.assertRaises(ContractError):load_request(canonical_bytes(d))
    def test_duplicate_json_key(self):
        with self.assertRaises(ContractError):load_request(b'{"source":{},"source":{}}')
    def test_float_json(self):
        d=self.request.to_dict();d['numericals'][0]['reported_lo']=0.1
        with self.assertRaises(ContractError):load_request(json.dumps(d).encode())
    def test_integer_where_string_expected(self):
        d=self.request.to_dict();d['numericals'][0]['reported_lo']=5
        with self.assertRaises(ContractError):load_request(canonical_bytes(d))
    def test_bool_in_integer_slot(self):
        d=asdict(self.policy);d['minimum_independent_assessors']=True
        with self.assertRaises(ContractError):load_policy(canonical_bytes(d))
    def test_path_traversal(self):
        d=self.request.to_dict();d['source']['sources'][0]['artifact']['path']='../escape'
        with self.assertRaises(ContractError):load_request(canonical_bytes(d))
    def test_malformed_payloads(self):
        for raw in (b'',b'{',b'\xff',b'NaN',b'Infinity',b'null',b'[]'):
            with self.subTest(raw=raw),self.assertRaises(ContractError):load_request(raw)
    def test_output_symlink_rejected(self):
        p=self.root/self.request.source.outputs[0].artifact.path;q=p.with_name('copy');q.write_bytes(p.read_bytes());p.unlink();p.symlink_to(q)
        self.assertEqual(self.run_check().status,'BLOCKED')
    def test_output_hardlink_rejected(self):
        p=self.root/self.request.source.outputs[0].artifact.path;os.link(p,p.with_name('hardlink'));self.assertEqual(self.run_check().status,'BLOCKED')
    def cli(self,output=None):
        rp=self.root/'request.json';pp=self.root/'policy.json';rp.write_bytes(canonical_bytes(self.request.to_dict()));pp.write_bytes(canonical_bytes(asdict(self.policy)))
        args=[sys.executable,'-B','-m','bie.qa.math_v2','--request',str(rp),'--policy',str(pp),'--artifact-root',str(self.root),'--as-of',str(NOW)]
        if output:args+=['--output',str(output)]
        return subprocess.run(args,cwd=ROOT,capture_output=True,timeout=15)
    def test_unsigned_cli_review_required(self):
        run=self.cli();self.assertEqual(run.returncode,3);self.assertEqual(json.loads(run.stdout)['status'],'REVIEW_REQUIRED');self.assertFalse(json.loads(run.stdout)['product_accepted'])
    def test_cli_no_overwrite(self):
        p=self.root/'old.json';p.write_text('KEEP');run=self.cli(p);self.assertEqual(run.returncode,4);self.assertEqual(p.read_text(),'KEEP')
    def test_cli_bad_input(self):
        p=self.root/'bad.json';p.write_text('{}');run=subprocess.run([sys.executable,'-B','-m','bie.qa.math_v2','--request',str(p),'--policy',str(p),'--artifact-root',str(self.root),'--as-of',str(NOW)],cwd=ROOT,capture_output=True,timeout=15)
        self.assertEqual(run.returncode,4);self.assertIn(b'MATH_JSON_FIELDS_MISMATCH',run.stderr)
    def test_duplicate_symbol_rejected_on_wire(self):
        d=asdict(self.policy);d=json.loads(canonical_bytes(d));d['scopes'][0]['symbols']*=2
        with self.assertRaises(ContractError):load_policy(canonical_bytes(d))

class AdapterTests(FixtureCase):
    def test_real_native_node(self):self.assertEqual(import_node(parse_expression(['x','+','2']),'x+2'),parse('x+2'))
    def test_native_parser_complete_expression_imports(self):
        node=parse_expression(['x','*','y','+','z'])
        self.assertEqual(import_node(node,'x*y+z'),parse('x*y+z'))
    def test_native_multitoken_atom_rejected(self):
        with self.assertRaises(ContractError):import_node(Node('atom','x+1'),'x+1')
    def test_native_fake_dict_rejected(self):
        with self.assertRaises(ContractError):import_node({'kind':'atom'},'x')
    def test_native_unknown_operator(self):
        with self.assertRaises(ContractError):import_node(Node('binary','eval',(Node('atom','x'),Node('atom','x'))),'x*x')
    def test_native_equation(self):self.assertEqual(import_equation(parse_equation('x+1=2')),eq('x+1','2'))
    def test_native_approximation_not_exact(self):
        with self.assertRaises(ContractError):import_equation(NativeEquation('x','≈','2'))
    def test_native_inequality_not_equality(self):
        with self.assertRaises(ContractError):import_equation(NativeEquation('x','<','2'))
    def test_actual_native_dimension_algebra(self):self.assertEqual(export_dimension((1,1,-2,0,0,0,0)).M,1)
    def test_native_bad_dimension(self):
        with self.assertRaises(ContractError):export_dimension((True,0,0,0,0,0,0))
    def test_native_chain_is_not_math_proof(self):
        result=inspect_native_chain((NativeStep('x=1','x=2'),NativeStep('x=2','x=3')))
        self.assertTrue(result['native']['valid']);self.assertFalse(result['mathematical_proof_available']);self.assertFalse(result['product_accepted'])
    def test_native_chain_break(self):self.assertFalse(inspect_native_chain((NativeStep('x=1','x=2'),NativeStep('y=2','x=3')))['native']['valid'])
    def test_native_float_status_not_exact_recomputation(self):
        r=inspect_native_numeric(1.0,1.0,0.0);self.assertTrue(r['native']['passed']);self.assertFalse(r['exact_recomputation_available'])
    def test_native_nan_rejected(self):
        with self.assertRaises(ContractError):inspect_native_numeric(float('nan'),1,1)
    def test_native_negative_tolerance_rejected(self):
        with self.assertRaises(ContractError):inspect_native_numeric(1,1,-1)
    def test_native_boolean_rejected(self):
        with self.assertRaises(ContractError):inspect_native_numeric(True,1,1)

class BridgeTests(FixtureCase):
    def prepare(self,r=None,c=None,**kw):
        r=r or self.request;return prepare_release_evidence(r,c or self.candidate,self.root,self.policy,as_of=NOW,**options(r,self.policy,**kw))
    def test_math_gate_stays_not_run(self):self.assertEqual(self.prepare().envelope.status,'NOT_RUN')
    def test_no_implicit_signature(self):self.assertEqual(self.prepare().envelope.signature,'');self.assertEqual(self.prepare().envelope.signer_key_id,'UNSIGNED')
    def test_report_hash(self):
        p=self.prepare();self.assertEqual(hashlib.sha256(p.report_bytes).hexdigest(),p.envelope.report.sha256)
    def test_candidate_binding(self):
        with self.assertRaises(ContractError):self.prepare(c=replace(self.candidate,run_id='another'))
    def test_artifact_binding(self):
        a=replace(self.candidate.artifacts[0],sha256='0'*64);c=replace(self.candidate,artifacts=(a,)+self.candidate.artifacts[1:]);r=replace(self.request,source=replace(self.request.source,candidate_digest=c.content_digest))
        with self.assertRaises(ContractError):self.prepare(r,c)
    def test_source_inventory_binding(self):
        a=artifact(self.root,'other-source.txt',b'Extra source','extra-source','source');c=replace(self.candidate,artifacts=self.candidate.artifacts+(a,));r=replace(self.request,source=replace(self.request.source,candidate_digest=c.content_digest))
        with self.assertRaises(ContractError):self.prepare(r,c)
    def test_numeric_error_exports_fail(self):
        n=replace(self.request.numericals[0],reported_lo='6',reported_hi='6');self.assertEqual(self.prepare(replace(self.request,numericals=(n,))).envelope.status,'FAIL')
    def test_full_release_blocked(self):
        p=self.prepare();dest=self.root/p.envelope.report.path;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(p.report_bytes)
        bundle=EvidenceBundle('2.0.0',self.candidate,(p.envelope,));r=ReleaseEvaluator().evaluate(bundle,self.root,as_of=NOW)
        self.assertEqual(r.release_status,'BLOCKED');self.assertFalse(r.product_accepted)
    def test_media_limit_in_report(self):self.assertFalse(json.loads(self.prepare().report_bytes)['actual_media_evaluated'])
