from dataclasses import replace, asdict
from pathlib import Path
import subprocess, sys, os, json
from sem_helpers import *
from bie.qa.semantic_v2.codec import load_request,load_policy,load_assessments
from bie.qa.semantic_v2.adapters import legacy_contradiction_hint,director_inventory,reasoning_findings
from bie.qa.semantic_v2.bridge import prepare_release_evidence
from bie.qa.release_v2.contracts import EvidenceBundle
from bie.qa.release_v2.evaluator import ReleaseEvaluator

ROOT=Path(__file__).resolve().parents[2]


class CodecTests(FixtureCase):
    def test_request_round_trip(self):self.assertEqual(load_request(canonical_bytes(self.request.to_dict())),self.request)
    def test_policy_round_trip(self):self.assertEqual(load_policy(canonical_bytes(self.policy.to_dict())),self.policy)
    def test_assessment_round_trip(self):
        aas=operational_simulation(self.request,self.policy)['assessments']
        self.assertEqual(load_assessments(canonical_bytes([asdict(a) for a in aas])),aas)
    def test_embedded_trust_field_rejected(self):
        d=self.request.to_dict();d['trusted']=True
        with self.assertRaises(ContractError):load_request(canonical_bytes(d))
    def test_duplicate_json_key_rejected(self):
        with self.assertRaises(ContractError):load_request(b'{"schema_version":"1.0.0","schema_version":"1.0.0"}')
    def test_float_json_rejected(self):
        d=self.request.to_dict();raw=json.dumps(d).replace('"depth": 2','"depth": 2.0').encode()
        with self.assertRaises(ContractError):load_request(raw)
    def test_null_collection_rejected(self):
        d=self.request.to_dict();d['normalizations']=None
        with self.assertRaises(ContractError):load_request(canonical_bytes(d))
    def test_nested_unknown_field_rejected(self):
        d=self.request.to_dict();d['normalizations'][0]['override']=True
        with self.assertRaises(ContractError):load_request(canonical_bytes(d))
    def test_malformed_json_and_unicode(self):
        for value in (b'not json',b'\xff',b'{',b'NaN'):
            with self.subTest(value=value),self.assertRaises(ContractError):load_request(value)
    def test_cli_offline_fail_closed(self):
        req=self.root/'request.json';pol=self.root/'policy.json'
        req.write_bytes(canonical_bytes(self.request.to_dict()));pol.write_bytes(canonical_bytes(self.policy.to_dict()))
        run=subprocess.run([sys.executable,'-B','-m','bie.qa.semantic_v2','--request',str(req),'--policy',str(pol),
            '--artifact-root',str(self.root),'--as-of',str(NOW)],cwd=ROOT,capture_output=True,timeout=15)
        self.assertEqual(run.returncode,2);self.assertEqual(json.loads(run.stdout)['status'],'BLOCKED')
        self.assertFalse(json.loads(run.stdout)['product_accepted'])
    def test_cli_invalid_input_exit(self):
        p=self.root/'bad.json';p.write_text('{}')
        run=subprocess.run([sys.executable,'-B','-m','bie.qa.semantic_v2','--request',str(p),'--policy',str(p),
            '--artifact-root',str(self.root),'--as-of',str(NOW)],cwd=ROOT,capture_output=True,timeout=15)
        self.assertEqual(run.returncode,64);self.assertFalse(run.stdout)


class AdapterTests(FixtureCase):
    def test_legacy_clear_cannot_promote_semantics(self):
        a={'claim_id':'a','subject':'lamp','predicate':'status','object':'on'};b={**a,'claim_id':'b'}
        r=legacy_contradiction_hint(a,b);self.assertEqual(r['legacy_result']['status'],'CLEAR')
        self.assertEqual(r['semantic_status'],'REVIEW_REQUIRED');self.assertFalse(r['may_authorize_release'])
    def test_legacy_conflict_is_advisory(self):
        a={'claim_id':'a','subject':'lamp','predicate':'color','object':'red'};b={**a,'claim_id':'b','object':'blue'}
        r=legacy_contradiction_hint(a,b);self.assertTrue(r['legacy_result']['contradiction']);self.assertFalse(r['may_authorize_release'])
    def test_legacy_missing_keys_rejected(self):
        with self.assertRaises(ContractError):legacy_contradiction_hint({'claim_id':'a'},{'claim_id':'b'})
    def lesson(self,review=False):
        from bie.director.lesson_architecture_contract import LessonSceneIntent,build_lesson_architecture
        return build_lesson_architecture('lesson','Title',(LessonSceneIntent('scene','Explain',('obj',),('cite-1',),requires_review=review),),('obj',),('book',),'1')
    def test_canonical_director_contract_consumed(self):
        lesson=self.lesson();r=director_inventory(lesson,(('obj','power'),))
        self.assertEqual(r.lesson_fingerprint,lesson.fingerprint());self.assertEqual(r.requirements[0].concept_id,'power')
        self.assertEqual(r.requirements[0].minimum_depth,2)
    def test_director_review_flag_preserved(self):self.assertTrue(director_inventory(self.lesson(True),(('obj','power'),)).requires_review)
    def test_director_mapping_scope_cannot_omit_objective(self):
        with self.assertRaises(ContractError):director_inventory(self.lesson(),())
    def test_edited_director_lesson_rejected(self):
        with self.assertRaises(ContractError):director_inventory(replace(self.lesson(),title=''),(('obj','power'),))
    def decision(self,review=False):
        from bie.reasoning.decision_contracts import ReasoningDecision,EvidenceRef
        return ReasoningDecision('decision','contradiction_resolution','lamp','Which?','retain','Preserve conflicting sources.',0.9,
            evidence_refs=[EvidenceRef('e1','primary',0.9),EvidenceRef('e2','contradicting',0.9)],requires_review=review)
    def test_canonical_reasoning_unresolved_preserved(self):
        from bie.reasoning.contradiction_resolution_qa import ContradictionResolution
        fs=reasoning_findings(self.decision(),(ContradictionResolution('conflict',('e1','e2'),'ESCALATED','Needs review'),))
        self.assertIn('UPSTREAM_UNRESOLVED_CONTRADICTION',{f.code for f in fs})
    def test_reasoning_resolution_not_substitute_for_semantics(self):
        from bie.reasoning.contradiction_resolution_qa import ContradictionResolution
        fs=reasoning_findings(self.decision(),(ContradictionResolution('conflict',('e1','e2'),'RESOLVED','Synthetic disposition','decision'),))
        self.assertEqual(fs,());self.assertNotEqual(self.run_case().status,'CHECKS_PASSED')
    def test_reasoning_review_remains_after_resolution(self):
        from bie.reasoning.contradiction_resolution_qa import ContradictionResolution
        fs=reasoning_findings(self.decision(True),(ContradictionResolution('conflict',('e1','e2'),'RESOLVED','Synthetic disposition','decision'),))
        self.assertIn('UPSTREAM_REASONING_REVIEW',{f.code for f in fs})
    def test_nonfinite_reasoning_data_rejected(self):
        for value in (float('nan'),float('inf'),True):
            with self.subTest(value=value),self.assertRaises(ContractError):reasoning_findings(replace(self.decision(),confidence=value),())


class BridgeTests(FixtureCase):
    def prepared(self,**options):
        return prepare_release_evidence(self.request,self.candidate,self.root,self.policy,as_of=NOW,
            **(operational_simulation(self.request,self.policy) if not options else options))
    def test_text_success_cannot_pass_media_gate(self):
        p=self.prepared();self.assertEqual(p.envelope.status,'NOT_RUN')
        self.assertIn('ACTUAL_MEDIA_SEMANTICS_NOT_EVALUATED',p.envelope.diagnostics)
    def test_report_bytes_hash_and_no_signature(self):
        p=self.prepared();self.assertEqual(hashlib.sha256(p.report_bytes).hexdigest(),p.envelope.report.sha256)
        self.assertEqual(p.envelope.signature,'');self.assertFalse(json.loads(p.report_bytes)['product_accepted'])
    def test_wrong_candidate_binding(self):
        c=replace(self.candidate,candidate_id='other')
        with self.assertRaises(ContractError):prepare_release_evidence(self.request,c,self.root,self.policy,as_of=NOW)
    def test_failed_semantics_produces_failed_gate(self):
        p=self.prepared(assessments=());self.assertEqual(p.envelope.status,'FAIL')
    def test_full_release_engine_keeps_blocked(self):
        p=self.prepared();target=self.root/p.envelope.report.path;target.parent.mkdir(parents=True);target.write_bytes(p.report_bytes)
        bundle=EvidenceBundle('2.0.0',self.candidate,(p.envelope,))
        r=ReleaseEvaluator().evaluate(bundle,self.root,as_of=NOW)
        self.assertEqual(r.release_status,'BLOCKED');self.assertFalse(r.product_accepted)
