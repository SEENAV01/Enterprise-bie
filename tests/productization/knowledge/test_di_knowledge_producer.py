"""Distinct authored Task029 controls; synthetic source, no semantic acceptance."""
from copy import deepcopy
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import secrets
import sqlite3
import sys
import tempfile
import time
import unittest
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/"tests/productization/document_intelligence"))
from structural_pdf_fixtures import structural_pdf
from apps.operator.contracts import Credentials,Principal,OperatorError,run_options
from apps.operator.service import Service
from apps.operator.knowledge_producer import KnowledgeProducerControlPlane
from bie.infrastructure.idempotency_store import IdempotencyError
from bie.infrastructure.artifact_store import BlobRef,ArtifactStoreError
from bie.model_gateway.model_interface import ModelResponse
from bie.model_gateway.provider_registry import ProviderRegistry,ProviderDescriptor
from bie.productization.contracts import *
from bie.productization.candidates import produce,validate_candidates,TechnicalSourceDerivedProvider
from bie.productization.durable_slice import *
from bie.document_intelligence.real_pdf_text_runtime import inspect_real_pdf_text


def document(text="Gravity attracts objects toward Earth."):
    return structured_document(inspect_real_pdf_text(structural_pdf(text_pages={0},text=text)),
                               "source-test","a"*64)


class ContractTests(unittest.TestCase):
    def setUp(self):self.doc=document();self.config=profile_config()
    def bad_doc(self, edit):
        copy=deepcopy(self.doc);edit(copy)
        with self.assertRaises(ProducerError):validate_document(copy)
    def bad_candidate(self, edit):
        payload=deepcopy(produce(self.doc,self.config)[0]);edit(payload)
        with self.assertRaises(ProducerError):validate_candidates(payload,self.doc)
    def test_actual_private_text(self):self.assertIn("Gravity",self.doc["blocks"][0]["text"])
    def test_real_source_anchors(self):self.assertEqual(self.doc["blocks"][0]["anchor"]["source_hash"],self.doc["source_sha256"])
    def test_source_change_changes_candidates(self):self.assertNotEqual(produce(self.doc,self.config)[0],produce(document("Plants absorb sunlight for growth."),self.config)[0])
    def test_no_prefilled_candidates(self):self.assertNotIn("concept_candidates",self.doc["blocks"][0]);self.assertTrue(produce(self.doc,self.config)[1]["nodes"])
    def test_verbatim_grounded_claims(self):
        for claim in produce(self.doc,self.config)[1]["claims"]:self.assertIn(claim["text"],self.doc["blocks"][0]["text"])
    def test_no_fabricated_relations(self):self.assertEqual(produce(self.doc,self.config)[1]["edges"],[])
    def test_missing_anchor(self):self.bad_candidate(lambda p:p["claims"][0].update(anchor_ids=[]))
    def test_foreign_anchor(self):self.bad_candidate(lambda p:p["claims"][0].update(anchor_ids=["foreign"]))
    def test_invented_claim(self):self.bad_candidate(lambda p:p["claims"][0].update(text="Invented unsupported fact"))
    def test_invented_concept(self):self.bad_candidate(lambda p:p["concepts"][0].update(label="Unstated"))
    def test_invalid_relation(self):self.bad_candidate(lambda p:p["relations"].append(dict(source="foreign",target="other",type="co_occurs",anchor_ids=[self.doc["blocks"][0]["anchor_id"]])))
    def test_self_loop(self):
        cid=produce(self.doc,self.config)[0]["concepts"][0]["concept_id"]
        self.bad_candidate(lambda p:p["relations"].append(dict(source=cid,target=cid,type="co_occurs",anchor_ids=[self.doc["blocks"][0]["anchor_id"]])))
    def test_unknown_candidate_field(self):self.bad_candidate(lambda p:p.update(secret="not permitted"))
    def test_empty_graph_not_success(self):self.bad_candidate(lambda p:p.update(concepts=[]))
    def test_duplicate_claim(self):self.bad_candidate(lambda p:p["claims"].append(p["claims"][0]))
    def test_invalid_schema(self):self.bad_doc(lambda p:p.update(schema="unknown"))
    def test_text_hash(self):self.bad_doc(lambda p:p["blocks"][0].update(text="Changed"))
    def test_foreign_source_hash(self):self.bad_doc(lambda p:p.update(source_sha256="b"*64))
    def test_anchor_identity(self):self.bad_doc(lambda p:p["blocks"][0].update(anchor_id="forged"))
    def test_geometry(self):self.bad_doc(lambda p:p["blocks"][0].update(geometry=[0,0,0,0]))
    def test_duplicate_block(self):self.bad_doc(lambda p:p["blocks"].append(p["blocks"][0]))
    def test_zero_pages(self):self.bad_doc(lambda p:p.update(page_count=0))
    def test_duplicate_json(self):
        with self.assertRaises(ProducerError):strict_json(b'{"a":1,"a":2}')
    def test_nonfinite_json(self):
        with self.assertRaises(ProducerError):strict_json(b'{"a":NaN}')
    def test_json_size(self):
        with self.assertRaises(ProducerError):strict_json(b" "*(MAX_ARTIFACT_BYTES+1))
    def test_private_contract(self):self.bad_doc(lambda p:p.update(privacy="PUBLIC"))
    def test_provider_missing(self):
        with self.assertRaisesRegex(ProducerError,"provider_unavailable"):produce(self.doc,profile_config("missing","missing"))
    def test_malformed_provider_response(self):
        class Broken:
            def invoke(self,r):return ModelResponse(TECHNICAL_PROVIDER,TECHNICAL_MODEL,"not json",{},"complete",{"evidence_kind":"TECHNICAL_SOURCE_DERIVED","live":False})
        registry=ProviderRegistry();registry.register(ProviderDescriptor(TECHNICAL_PROVIDER,TECHNICAL_MODEL,frozenset({"structured_knowledge"})),Broken())
        with self.assertRaises(ProducerError):produce(self.doc,self.config,registry)
    def test_safe_receipt_no_text(self):
        receipt=produce(self.doc,self.config)[2]
        self.assertNotIn(self.doc["blocks"][0]["text"],json.dumps(receipt));self.assertFalse(receipt["live_provider_executed"])
    def test_provider_timeout_safe_code(self):
        class Timeout:
            def invoke(self,request):raise TimeoutError("private provider diagnostic")
        registry=ProviderRegistry()
        registry.register(ProviderDescriptor(TECHNICAL_PROVIDER,TECHNICAL_MODEL,frozenset({"structured_knowledge"})),Timeout())
        with self.assertRaisesRegex(ProducerError,"^provider_timeout$"):produce(self.doc,self.config,registry)
    def test_partial_semantics_explicit(self):self.assertFalse(produce(self.doc,self.config)[1]["academic_acceptance"])
    def test_case_variants_do_not_duplicate_anchor(self):
        graph=produce(document("Gravity gravity GRAVITY attracts objects."),self.config)[1]
        for node in graph["nodes"].values():self.assertEqual(len(node["anchor_ids"]),len(set(node["anchor_ids"])))
    def test_page_map_binding(self):self.bad_doc(lambda p:p["blocks"][0]["page_map"].update(region_id="foreign"))
    def test_unknown_document_field(self):self.bad_doc(lambda p:p.update(secret="forbidden"))
    def test_runtime_identity_required(self):self.bad_doc(lambda p:p.update(runtime_identity="unknown"))


class DurableTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        self.credentials=Credentials();self.token=secrets.token_urlsafe(40)
        self.p=Principal("test","tenant",frozenset({"read","source","create","worker","control","admin_recover"}),time.time()+300)
        self.credentials.grant(self.token,self.p)
        self.operator=Service(self.root,self.credentials)
        self.port=KnowledgeProducerControlPlane(self.operator,enabled_profiles={PROFILE})
        self.source=self.operator.import_pdf(self.p,structural_pdf(text_pages={0},text="Gravity attracts objects toward Earth."))
        self.run=self.port.admit(self.p,self.source["source_id"],"intent")["run_id"]
    def tearDown(self):self.tmp.cleanup()
    def complete(self):
        result=None
        for _ in range(3):result=self.port.work_once(self.p,self.run)
        return result
    def test_three_stages(self):self.assertEqual(self.complete()["stages"],{s:"SUCCEEDED" for s in STAGES})
    def test_graph_persisted(self):self.assertGreater(self.complete()["knowledge"]["concept_count"],0)
    def test_projection_no_source_text(self):self.assertNotIn("Gravity",json.dumps(self.complete()))
    def test_downstream_not_run(self):self.assertTrue(all(s=="NOT_RUN" for s in self.complete()["downstream"].values()))
    def test_queue_all_acked(self):
        self.complete()
        with self.port.native(self.p,self.run,"read") as n:self.assertEqual(n.queue.stats()["ACKED"],3)
    def test_idempotent_replay(self):self.assertEqual(self.port.admit(self.p,self.source["source_id"],"intent")["run_id"],self.run)
    def test_conflicting_source(self):
        other=self.operator.import_pdf(self.p,structural_pdf(text_pages={0},text="Plants absorb sunlight."))
        with self.assertRaises(IdempotencyError):self.port.admit(self.p,other["source_id"],"intent")
    def test_conflicting_provider(self):
        with self.assertRaises(IdempotencyError):self.port.admit(self.p,self.source["source_id"],"intent",provider="missing",model="missing")
    def test_restart_readback(self):
        final=self.complete()
        reopened=KnowledgeProducerControlPlane(Service(self.root,self.credentials),enabled_profiles={PROFILE})
        self.assertEqual(reopened.status(self.p,self.run),final)
    def test_worker_absent_ready_durable(self):
        reopened=KnowledgeProducerControlPlane(Service(self.root,self.credentials),enabled_profiles={PROFILE})
        self.assertEqual(reopened.status(self.p,self.run)["stages"]["SOURCE"],"READY")
    def test_provider_unavailable_blocked(self):
        run=self.port.admit(self.p,self.source["source_id"],"missing",provider="missing",model="missing")["run_id"]
        for _ in range(3):result=self.port.work_once(self.p,run)
        self.assertEqual(result["stages"]["KNOWLEDGE"],"BLOCKED");self.assertIsNone(result["knowledge"])
    def test_foreign_tenant_source(self):
        foreign=Principal("foreign","foreign",self.p.permissions,time.time()+100)
        self.credentials.grant(secrets.token_urlsafe(40),foreign)
        with self.assertRaises(OperatorError):self.port.admit(foreign,self.source["source_id"],"foreign")
    def test_foreign_run(self):
        with self.port.native(self.p,self.run,"read") as n:
            with self.assertRaises(ProducerError):n.status(self.run,"foreign")
    def test_revoked_principal(self):
        self.credentials.revoke(self.token)
        with self.assertRaises(OperatorError):self.port.work_once(self.p,self.run)
    def test_profile_requires_enablement(self):
        with self.assertRaises(OperatorError):KnowledgeProducerControlPlane(self.operator).status(self.p,self.run)
    def test_inspection_profile_unchanged(self):
        self.assertEqual(run_options({})["profile"],"native_pdf_inspection_v1")
        with self.assertRaises(OperatorError):run_options({"profile":PROFILE})
    def test_inspection_worker_capability_isolation(self):
        with self.port.native(self.p,self.run,"read") as n:self.assertIsNone(n.queue.poll("old",capability_tags=["pdf_inspection"]))
    def test_explicit_unsupported_controls(self):
        with self.assertRaisesRegex(ProducerError,"producer_control_not_supported"):self.port.control(self.p,self.run,"cancel")
    def test_cas_tamper(self):
        final=self.complete()
        path=self.operator.cas._path(final["knowledge"]["sha256"]);path.write_bytes(b"tampered")
        with self.assertRaises(Exception):self.port.status(self.p,self.run)
    def test_metadata_cannot_rebind_artifact_digest(self):
        final=self.complete()
        with self.port.native(self.p,self.run,"read") as n:
            blob=n.cas.put_bytes(canonical({"replacement":True}))
            with n.persistence._conn() as db:
                db.execute("UPDATE artifact_records SET blob_digest=?,blob_size=? WHERE artifact_id=?",
                    (blob.digest,blob.size,final["knowledge"]["artifact_id"]))
            with self.assertRaisesRegex(ProducerError,"artifact_identity_mismatch"):n.status(self.run,self.p.tenant)
    def test_safe_projection_has_source_pages_and_concept_ids(self):
        summary=self.complete()["knowledge"]
        self.assertEqual(summary["source_pages"],[1])
        self.assertEqual(len(summary["concept_ids"]),summary["concept_count"])
        self.assertNotIn("Gravity",json.dumps(summary))
    def test_audit_capacity_blocks_before_native_work(self):
        from dataclasses import replace
        with self.operator.catalog.tx(read_only=True) as db:
            events=self.operator.catalog.budget.inventory(db)["events"]
        self.operator.catalog.budget=replace(self.operator.catalog.budget,max_events=events)
        with self.assertRaises(OperatorError):self.port.work_once(self.p,self.run)
        self.assertEqual(self.port.status(self.p,self.run)["stages"]["SOURCE"],"READY")
    def test_source_tamper(self):
        self.operator.cas._path(self.source["sha256"]).write_bytes(b"tampered")
        with self.assertRaises(Exception):self.port.admit(self.p,self.source["source_id"],"new")
    def test_private_document_registered(self):
        self.complete()
        with self.port.native(self.p,self.run,"read") as n:
            state=n.persistence.load_run_state(self.run);ref=state["stages"]["DOCUMENT_INTELLIGENCE"]["attempts"][-1]["output_artifact_refs"][0]
            self.assertIn("Gravity",n.read(self.run,ref)["blocks"][0]["text"])
    def test_evidence_no_text_or_paths(self):
        self.complete()
        with self.port.native(self.p,self.run,"read") as n:
            for ref in n.persistence.evidence_for_run(self.run):
                raw=json.dumps(n.read(self.run,ref));self.assertNotIn("Gravity",raw);self.assertNotIn(str(self.root),raw)
    def test_lineage_source_document_candidate_graph(self):
        result=self.complete()
        with self.port.native(self.p,self.run,"read") as n:
            graph=n.record(self.run,result["knowledge"]["artifact_id"])
            self.assertEqual(len(graph.parent_artifact_ids),2)
            self.assertEqual({n.record(self.run,p).artifact_type for p in graph.parent_artifact_ids},{"document.structured","knowledge.candidates"})
    def test_source_evidence_parents_unique(self):
        self.complete()
        with self.port.native(self.p,self.run,"read") as n:
            for ref in n.persistence.evidence_for_run(self.run):
                parents=n.record(self.run,ref).parent_artifact_ids
                self.assertEqual(len(parents),len(set(parents)))
    def test_di_evidence_records_native_policy_and_packages(self):
        self.complete()
        with self.port.native(self.p,self.run,"read") as n:
            attempt=n.persistence.load_run_state(self.run)["stages"]["DOCUMENT_INTELLIGENCE"]["attempts"][-1]
            receipt=n.read(self.run,attempt["evidence_refs"][0])
            self.assertEqual(receipt["document_schema"],DOCUMENT_SCHEMA)
            self.assertEqual(set(receipt["packages"]),{"pypdf","pdfplumber"})
            self.assertTrue(receipt["reading_order_policy"])
    def test_admission_rechecks_authorization_at_commit_boundary(self):
        from bie.productization.durable_slice import run_identity
        run=run_identity(self.p.tenant,"revoked-admission")
        def fault(phase):
            if phase=="after_source_admission":self.credentials.revoke(self.token)
        with self.assertRaises(OperatorError):
            with self.port.native(self.p,run,"create",fault=fault) as n:
                source=dict(source_id=self.source["source_id"],sha256=self.source["sha256"],
                    size_bytes=self.source["byte_length"],media_type="application/pdf",tenant=self.p.tenant,
                    privacy="PRIVATE_LOCAL_CAS",rights="LOCAL_PROCESSING_ONLY")
                n.admit(source,self.p.tenant,"revoked-admission")
    def test_stale_lease_rejected(self):
        with self.port.native(self.p,self.run,"read") as n:
            old=n.leases.acquire("test","fingerprint","old",now=0,ttl_seconds=1)
            n.leases.acquire("test","fingerprint","new",now=2,ttl_seconds=1)
            with self.assertRaises(Exception):n.leases.assert_active(old,now=2)
    def test_live_competing_lease_rejected(self):
        with self.port.native(self.p,self.run,"read") as n:
            n.leases.acquire("test","fingerprint","old",ttl_seconds=30)
            with self.assertRaises(Exception):n.leases.acquire("test","fingerprint","new",ttl_seconds=30)
    def test_terminal_before_next_admission_recovery(self):
        class Crash(BaseException):pass
        def fault(phase):
            if phase=="before_next_admission":raise Crash()
        with self.assertRaises(Crash):self.port.work_once(self.p,self.run,fault=fault)
        result=self.complete();self.assertTrue(result["slice_complete"])
    def test_empty_native_text_fails_closed(self):
        source=self.operator.import_pdf(self.p,structural_pdf())
        run=self.port.admit(self.p,source["source_id"],"empty")["run_id"]
        self.port.work_once(self.p,run);result=self.port.work_once(self.p,run)
        self.assertEqual(result["stages"]["DOCUMENT_INTELLIGENCE"],"FAILED")
        self.assertIsNone(result["knowledge"])


if __name__=="__main__":unittest.main()
