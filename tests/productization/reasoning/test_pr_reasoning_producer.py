"""Task030 distinct positive/seeded negative controls, native synthetic source."""
from copy import deepcopy
import gc
import json
from pathlib import Path
import secrets
import sys
import tempfile
import time
import unittest
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/"tests/productization/document_intelligence"))
from structural_pdf_fixtures import structural_pdf,styled_text_pdf
from apps.operator.contracts import Credentials,Principal,OperatorError,run_options
from apps.operator.service import Service
from apps.operator.knowledge_producer import KnowledgeProducerControlPlane
from apps.operator.reasoning_producer import ReasoningProducerControlPlane
from bie.productization.contracts import (structured_document,canonical,digest,ProducerError,PROFILE as OLD_PROFILE,profile_config as old_config)
from bie.productization.candidates import produce
from bie.productization.durable_slice import run_identity,CAPABILITY as OLD_CAPABILITY
from bie.productization.pr_reasoning import *
from bie.productization.reasoning_slice import STAGES
from bie.document_intelligence.real_pdf_text_runtime import inspect_real_pdf_text
from bie.model_gateway.model_interface import ModelResponse
from bie.model_gateway.provider_registry import ProviderRegistry,ProviderDescriptor


def inputs(text="Birds requires Flight."):
    doc=structured_document(inspect_real_pdf_text(structural_pdf(text_pages={0},text=text)),"source-test","a"*64)
    knowledge=produce(doc,old_config())[1]
    context=binding("prod-test",doc["source_sha256"],"artifact-knowledge",digest(knowledge),1)
    pr=prerequisite_artifact(knowledge,context)
    return doc,knowledge,context,pr


class ContractTests(unittest.TestCase):
    def setUp(self):self.doc,self.k,self.context,self.pr=inputs()
    def bad_pr(self,edit):
        value=deepcopy(self.pr);edit(value)
        with self.assertRaises(ProducerError):verify_prerequisite(value,self.k,self.context)
    def bad_re(self,edit):
        value=reasoning_artifact(self.k,self.pr,self.context,"artifact-pr",self.doc)
        edit(value)
        with self.assertRaises(ProducerError):verify_reasoning(value,self.k,self.pr,self.context,"artifact-pr",self.doc)
    def test_native_knowledge_input(self):self.assertTrue(verify_knowledge(self.k,self.doc))
    def test_explicit_source_edge(self):self.assertEqual(len(self.pr["edges"]),1)
    def test_source_change_changes_output(self):self.assertNotEqual(self.pr,inputs("Plants requires Light.")[3])
    def test_no_prefilled_prerequisite(self):self.assertNotIn("prerequisites",self.k);self.assertTrue(self.pr["edges"])
    def test_document_order_is_not_dependency(self):self.assertEqual(inputs("Birds Flight Forest.")[3]["edges"],[])
    def test_claim_and_anchor_bound(self):
        edge=self.pr["edges"][0];self.assertIn(edge["claim_id"],{c["claim_id"] for c in self.k["claims"]})
        self.assertTrue(set(edge["anchor_ids"])<=set(self.k["claims"][0]["anchor_ids"]))
    def test_foreign_concept(self):self.bad_pr(lambda p:p["edges"][0].update(prerequisite="foreign"))
    def test_self_edge(self):self.bad_pr(lambda p:p["edges"][0].update(prerequisite=p["edges"][0]["dependent"]))
    def test_reverse_edge(self):
        self.bad_pr(lambda p:p["edges"][0].update(prerequisite=p["edges"][0]["dependent"],dependent=p["edges"][0]["prerequisite"]))
    def test_foreign_anchor(self):self.bad_pr(lambda p:p["edges"][0].update(anchor_ids=["foreign"]))
    def test_missing_anchor(self):self.bad_pr(lambda p:p["edges"][0].update(anchor_ids=[]))
    def test_invented_claim(self):self.bad_pr(lambda p:p["edges"][0].update(claim_id="invented"))
    def test_invalid_confidence(self):self.bad_pr(lambda p:p["edges"][0].update(confidence=1.0))
    def test_cycle_fails_closed(self):
        with self.assertRaisesRegex(ProducerError,"prerequisite_cycle"):inputs("Birds requires Flight. Flight requires Birds.")
    def test_self_source_fails_closed(self):
        with self.assertRaisesRegex(ProducerError,"prerequisite_self_edge"):inputs("Birds requires Birds.")
    def test_unsupported_candidate_review(self):self.assertTrue(inputs("Birds requires ocean habitat.")[3]["review"])
    def test_stable_teaching_order(self):self.assertEqual(self.pr["order"],prerequisite_artifact(self.k,self.context)["order"])
    def test_teaching_order_dependency_direction(self):
        e=self.pr["edges"][0];self.assertLess(self.pr["order"].index(e["prerequisite"]),self.pr["order"].index(e["dependent"]))
    def test_foreign_run(self):self.bad_pr(lambda p:p.update(run_id="foreign"))
    def test_foreign_graph(self):self.bad_pr(lambda p:p.update(knowledge_sha256="b"*64))
    def test_foreign_knowledge_artifact(self):self.bad_pr(lambda p:p.update(knowledge_artifact_id="foreign"))
    def test_schema(self):self.bad_pr(lambda p:p.update(schema="unknown"))
    def test_unknown_field(self):self.bad_pr(lambda p:p.update(private_secret="forbidden"))
    def test_nonmath_reasoning(self):self.assertTrue(reasoning_artifact(self.k,self.pr,self.context,"artifact-pr",self.doc)["decisions"])
    def test_reasoning_exact_pr_identity(self):self.bad_re(lambda r:r.update(prerequisite_artifact_id="foreign"))
    def test_reasoning_exact_knowledge(self):self.bad_re(lambda r:r.update(knowledge_sha256="b"*64))
    def test_reasoning_foreign_claim(self):self.bad_re(lambda r:r["source_claim_ids"].append("invented"))
    def test_reasoning_missing_anchor(self):self.bad_re(lambda r:r.update(source_anchor_ids=[]))
    def test_reasoning_foreign_anchor(self):self.bad_re(lambda r:r["source_anchor_ids"].append("invented"))
    def test_unsupported_causal(self):self.bad_re(lambda r:r["decisions"][0].update(decision_type="causal_explanation"))
    def test_unsupported_temporal(self):self.bad_re(lambda r:r.update(executed_types=["temporal"]))
    def test_unsupported_spatial(self):self.bad_re(lambda r:r.update(executed_types=["spatial"]))
    def test_uncertainty_not_certainty(self):self.bad_re(lambda r:r["decisions"][0].update(confidence=1.0,requires_review=False))
    def test_missing_evidence(self):self.bad_re(lambda r:r["decisions"][0].update(evidence_refs=[]))
    def test_reasoning_upstream_change(self):
        other=inputs("Plants requires Light.")
        self.assertNotEqual(reasoning_artifact(self.k,self.pr,self.context,"artifact-pr",self.doc),reasoning_artifact(other[1],other[3],other[2],"artifact-pr",other[0]))
    def test_math_equation_blocked(self):
        doc,k,c,p=inputs("Calculate velocity using v = d / t.")
        with self.assertRaisesRegex(ProducerError,"math_evidence_required"):reasoning_artifact(k,p,c,"artifact-pr",doc)
    def test_math_units_blocked(self):self.assertTrue(math_required(inputs("Mass is 12 kg.")[0]))
    def test_math_proof_blocked(self):self.assertTrue(math_required(inputs("Proof of the theorem is required.")[0]))
    def test_math_beyond_ki_excerpt(self):
        text="Birds Flight Forest. "+"ordinary prose "*45+" Calculate x = 2."
        # The original one-line 12pt fixture overflowed the physical page and
        # canonical DI correctly rejected it. Use a genuine in-page tiny-font
        # boundary fixture; do not weaken native geometry/source validation.
        doc=structured_document(inspect_real_pdf_text(styled_text_pdf([[(72,720,text,1.0,False)]])),"source-test","a"*64)
        self.assertGreater(doc["blocks"][0]["text"].index("="),512)
        self.assertTrue(math_required(doc))
    def test_gateway_source_change(self):
        first=gateway_candidate("PREREQUISITE",self.k,self.doc,profile_config())[0]
        doc,k,c,p=inputs("Plants requires Light.")
        self.assertNotEqual(first,gateway_candidate("PREREQUISITE",k,doc,profile_config())[0])
    def test_gateway_unavailable(self):
        with self.assertRaisesRegex(ProducerError,"provider_unavailable"):gateway_candidate("PREREQUISITE",self.k,self.doc,profile_config(),registry=ProviderRegistry())
    def fake(self,content=None,error=None):
        class Fake:
            def invoke(self,request):
                if error:raise error
                return ModelResponse(PROVIDER,MODEL,content,{},"complete",{"evidence_kind":"TECHNICAL_SOURCE_DERIVED","live":False})
        r=ProviderRegistry();r.register(ProviderDescriptor(PROVIDER,MODEL,frozenset({"grounded_pr_reasoning"})),Fake());return r
    def test_gateway_malformed(self):
        with self.assertRaises(ProducerError):gateway_candidate("PREREQUISITE",self.k,self.doc,profile_config(),registry=self.fake("{broken"))
    def test_gateway_timeout(self):
        with self.assertRaisesRegex(ProducerError,"provider_timeout"):gateway_candidate("PREREQUISITE",self.k,self.doc,profile_config(),registry=self.fake(error=TimeoutError()))
    def test_gateway_provider_error_cannot_leak_source(self):
        with self.assertRaises(ProducerError) as caught:
            gateway_candidate("PREREQUISITE",self.k,self.doc,profile_config(),
                registry=self.fake(error=ProducerError("Birds requires Flight. private provider detail")))
        self.assertEqual(caught.exception.code,"provider_execution_failed")
        self.assertNotIn("Birds",str(caught.exception))
    def test_gateway_invented_relationship(self):
        with self.assertRaises(ProducerError):gateway_candidate("PREREQUISITE",self.k,self.doc,profile_config(),registry=self.fake('{"edges":[],"order":[],"review":[],"roots":[]}'))
    def test_global_math_stage_not_invented(self):
        from bie.infrastructure.execution_graph import default_enterprise_graph
        self.assertNotIn("MATH",default_enterprise_graph().stages)


class DurableTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        self.credentials=Credentials();self.token=secrets.token_urlsafe(40)
        self.p=Principal("test","local",frozenset({"read","source","create","worker","control","admin_recover"}),time.time()+360)
        self.credentials.grant(self.token,self.p);self.operator=Service(self.root,self.credentials)
        self.port=ReasoningProducerControlPlane(self.operator,enabled_profiles={PROFILE})
        self.source=self.operator.import_pdf(self.p,structural_pdf(text_pages={0},text="Birds requires Flight."))
        self.run=self.port.admit(self.p,self.source["source_id"],"intent")["run_id"]
    def tearDown(self):gc.collect();self.tmp.cleanup()
    def complete(self):
        for _ in range(5):result=self.port.work_once(self.p,self.run)
        return result
    def test_five_stages(self):self.assertEqual(self.complete()["stages"],{s:"SUCCEEDED" for s in STAGES})
    def test_graph_and_decisions_persisted(self):
        r=self.complete();self.assertEqual(r["prerequisite"]["edge_count"],1);self.assertEqual(r["reasoning"]["decision_count"],1)
    def test_pedagogy_not_run(self):self.assertEqual(self.complete()["downstream"]["PEDAGOGY"],"NOT_RUN")
    def test_safe_projection(self):self.assertNotIn("Birds",json.dumps(self.complete()))
    def test_all_queue_acked(self):
        self.complete()
        with self.port.native(self.p,self.run,"read") as n:self.assertEqual(n.queue.stats()["ACKED"],5)
    def test_task028_isolation(self):
        with self.port.native(self.p,self.run,"read") as n:self.assertIsNone(n.queue.poll("old",capability_tags=["pdf_inspection"]))
    def test_task029_worker_isolation(self):
        with self.port.native(self.p,self.run,"read") as n:self.assertIsNone(n.queue.poll("old",capability_tags=[OLD_CAPABILITY]))
    def test_replay(self):self.assertEqual(self.port.admit(self.p,self.source["source_id"],"intent")["run_id"],self.run)
    def test_conflicting_intent(self):
        other=self.operator.import_pdf(self.p,structural_pdf(text_pages={0},text="Plants requires Light."))
        with self.assertRaises(Exception):self.port.admit(self.p,other["source_id"],"intent")
    def test_restart(self):
        final=self.complete();reopened=ReasoningProducerControlPlane(Service(self.root,self.credentials),enabled_profiles={PROFILE})
        self.assertEqual(reopened.status(self.p,self.run),final)
    def test_native_inspection_profile_preserved(self):self.assertEqual(run_options({})["profile"],"native_pdf_inspection_v1")
    def test_profile_requires_enablement(self):
        with self.assertRaises(OperatorError):ReasoningProducerControlPlane(self.operator).status(self.p,self.run)
    def test_foreign_tenant(self):
        with self.port.native(self.p,self.run,"read") as n:
            with self.assertRaises(ProducerError):n.status(self.run,"foreign")
    def test_revoked(self):
        self.credentials.revoke(self.token)
        with self.assertRaises(OperatorError):self.port.work_once(self.p,self.run)
    def test_unsupported_cancel(self):
        with self.assertRaisesRegex(ProducerError,"producer_control_not_supported"):self.port.control(self.p,self.run,"cancel")
    def test_math_blocks_real_stage(self):
        source=self.operator.import_pdf(self.p,structural_pdf(text_pages={0},text="Calculate velocity using v = d / t."))
        run=self.port.admit(self.p,source["source_id"],"math")["run_id"]
        for _ in range(5):r=self.port.work_once(self.p,run)
        self.assertEqual(r["stages"]["REASONING"],"BLOCKED");self.assertIsNone(r["reasoning"])
        self.assertEqual(r["safe_diagnostics"],{"REASONING":["math_evidence_required"]})
    def test_provider_missing_blocks_pr(self):
        for _ in range(3):self.port.work_once(self.p,self.run)
        r=self.port.work_once(self.p,self.run,continuation_registry=ProviderRegistry())
        self.assertEqual(r["stages"]["PREREQUISITE"],"BLOCKED");self.assertEqual(r["stages"]["REASONING"],"PENDING")
    def test_pr_tamper(self):
        r=self.complete();self.operator.cas._path(r["prerequisite"]["sha256"]).write_bytes(b"tampered")
        with self.assertRaises(Exception):self.port.status(self.p,self.run)
    def test_re_tamper(self):
        r=self.complete();self.operator.cas._path(r["reasoning"]["sha256"]).write_bytes(b"tampered")
        with self.assertRaises(Exception):self.port.status(self.p,self.run)
    def test_knowledge_tamper_blocks_admission(self):
        for _ in range(3):r=self.port.work_once(self.p,self.run)
        self.operator.cas._path(r["knowledge"]["sha256"]).write_bytes(b"tampered")
        with self.assertRaises(Exception):self.port.work_once(self.p,self.run)
    def test_metadata_foreign_run(self):
        r=self.complete()
        with self.port.native(self.p,self.run,"read") as n:
            with n.persistence._conn() as db:db.execute("UPDATE artifact_records SET run_id='foreign' WHERE artifact_id=?",(r["prerequisite"]["artifact_id"],))
            with self.assertRaisesRegex(ProducerError,"foreign_artifact"):n.status(self.run,self.p.tenant)
    def test_safe_failure_receipt(self):
        for _ in range(3):self.port.work_once(self.p,self.run)
        self.port.work_once(self.p,self.run,continuation_registry=ProviderRegistry())
        with self.port.native(self.p,self.run,"read") as n:
            for ref in n.persistence.evidence_for_run(self.run):self.assertNotIn("Birds",canonical(n.read(self.run,ref)).decode())
    def test_original_profiles_still_three_stages(self):
        old=KnowledgeProducerControlPlane(self.operator,enabled_profiles={OLD_PROFILE})
        run=old.admit(self.p,self.source["source_id"],"old")["run_id"]
        for _ in range(3):r=old.work_once(self.p,run)
        self.assertEqual(set(r["stages"]),set(STAGES[:3]));self.assertTrue(r["slice_complete"])
    def test_extend_completed_retains_identity(self):
        old=KnowledgeProducerControlPlane(self.operator,enabled_profiles={OLD_PROFILE})
        run=old.admit(self.p,self.source["source_id"],"old")["run_id"]
        for _ in range(3):r=old.work_once(self.p,run)
        before=r["knowledge"];self.assertEqual(self.port.continue_completed(self.p,run)["run_id"],run)
        for _ in range(2):after=self.port.work_once(self.p,run)
        self.assertTrue(after["slice_complete"]);self.assertEqual(after["knowledge"],before)
        self.assertEqual(self.port.continue_completed(self.p,run)["run_id"],run)
        # Explicit scope evolution cannot silently masquerade as the old profile.
        with self.assertRaisesRegex(ProducerError,"producer_profile_scope_mismatch"):old.status(self.p,run)
    def test_unfinished_legacy_run_cannot_continue(self):
        old=KnowledgeProducerControlPlane(self.operator,enabled_profiles={OLD_PROFILE})
        run=old.admit(self.p,self.source["source_id"],"old-ready")["run_id"]
        with self.assertRaisesRegex(ProducerError,"knowledge_not_succeeded"):self.port.continue_completed(self.p,run)


if __name__=="__main__":unittest.main()
