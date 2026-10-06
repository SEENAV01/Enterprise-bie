"""Distinct Task031 source-derived technical controls; no academic acceptance."""
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
from structural_pdf_fixtures import positioned_text_pdf
from apps.operator.contracts import Credentials, Principal, run_options
from apps.operator.service import Service
from apps.operator.math_producer import MathProducerControlPlane
from apps.operator.knowledge_producer import KnowledgeProducerControlPlane
from apps.operator.reasoning_producer import ReasoningProducerControlPlane
from bie.infrastructure.execution_graph import default_enterprise_graph, legacy_enterprise_graph_v1, EnterpriseGraphError
from bie.productization.contracts import structured_document, digest, ProducerError, canonical, PROFILE as OLD_PROFILE
from bie.productization.candidates import produce
from bie.productization.pr_reasoning import prerequisite_artifact, profile_config as pr_config, PROFILE as PR_PROFILE
from bie.productization.math_evidence import *
from bie.productization.math_slice import STAGES
from bie.document_intelligence.real_pdf_text_runtime import inspect_real_pdf_text


def pdf(lines=()):
    return positioned_text_pdf([[(72,740-40*i,text) for i,text in enumerate(("Birds requires Flight.",)+tuple(lines))]])


def inputs(lines=()):
    doc=structured_document(inspect_real_pdf_text(pdf(lines)),"source-test","a"*64)
    k=produce(doc,profile_config())[1]
    b=binding("prod-test",doc["source_sha256"],"artifact-knowledge",digest(k),1)
    p=prerequisite_artifact(k,b)
    m=math_artifact(doc,k,p,b,"artifact-document","artifact-pr")
    return doc,k,p,b,m


class GraphTests(unittest.TestCase):
    def test_math_present(self):self.assertIn("MATH",default_enterprise_graph().stages)
    def test_dependency_position(self):
        g=default_enterprise_graph();self.assertTrue(g._direct_edge("PREREQUISITE","MATH"));self.assertTrue(g._direct_edge("MATH","REASONING"))
    def test_math_inputs(self):self.assertEqual(default_enterprise_graph().stages["MATH"].consumes,["document.structured","knowledge.graph","prerequisite.graph"])
    def test_reasoning_requires_math(self):self.assertIn("MATH",default_enterprise_graph().stages["REASONING"].required_predecessors)
    def test_math_removal_rejected(self):
        g=default_enterprise_graph();del g.stages["MATH"]
        with self.assertRaises(EnterpriseGraphError):g.validate()
    def test_reasoning_direct_bypass_rejected(self):
        g=default_enterprise_graph();g.edges["PREREQUISITE"].append("REASONING")
        with self.assertRaises(EnterpriseGraphError):g.validate()
    def test_math_artifact_bypass_rejected(self):
        from dataclasses import replace
        g=default_enterprise_graph();g.stages["REASONING"]=replace(g.stages["REASONING"],consumes=["knowledge.graph","prerequisite.graph"])
        with self.assertRaises(EnterpriseGraphError):g.validate()
    def test_legacy_graph_pinned(self):self.assertNotIn("MATH",legacy_enterprise_graph_v1().stages)
    def test_audio_not_invented(self):self.assertNotIn("AUDIO",default_enterprise_graph().stages)
    def test_existing_source_bypass_rejected(self):
        g=default_enterprise_graph();g.edges["SOURCE"].append("VIDEO_CODE")
        with self.assertRaises(EnterpriseGraphError):g.validate()


class MathContractTests(unittest.TestCase):
    def setUp(self):self.doc,self.k,self.p,self.b,self.m=inputs(("2 + 3 = 5",))
    def bad(self,edit):
        m=deepcopy(self.m);edit(m)
        with self.assertRaises(ProducerError):verify_math(m,self.doc,self.k,self.p,self.b,"artifact-document","artifact-pr")
    def test_real_pdf_text_drives_equation(self):self.assertEqual(self.m["equations"][0]["original_expression"],"2 + 3 = 5")
    def test_native_math_pipeline(self):self.assertEqual(self.m["equations"][0]["relation"],"=")
    def test_source_change_changes_math(self):self.assertNotEqual(digest(self.m),digest(inputs(("3 + 4 = 7",))[-1]))
    def test_no_prefilled_math(self):self.assertNotIn("equations",self.doc);self.assertTrue(self.m["equations"])
    def test_exact_numerical_certificate(self):self.assertEqual(self.m["equations"][0]["proof"],"EXACT_RATIONAL_NUMERICAL_EQUALITY")
    def test_numerical_counterexample(self):self.assertEqual(inputs(("2 + 3 = 6",))[-1]["applicability"],"REVIEW_REQUIRED")
    def test_symbolic_certificate(self):
        m=inputs(("Symbols: x dimensionless.","x + x = 2 * x"))[-1]
        self.assertEqual(m["equations"][0]["proof"],"EXACT_RATIONAL_POLYNOMIAL_IDENTITY")
    def test_symbols_retained(self):self.assertEqual(inputs(("Symbols: x dimensionless.","x + x = 2 * x"))[-1]["equations"][0]["symbols"],["x"])
    def test_undeclared_symbol_review(self):self.assertEqual(inputs(("x + x = 2 * x",))[-1]["applicability"],"REVIEW_REQUIRED")
    def test_false_symbolic_identity(self):self.assertEqual(inputs(("Symbols: x dimensionless.","x + x = 3 * x"))[-1]["applicability"],"REVIEW_REQUIRED")
    def test_unsafe_expression_review(self):self.assertEqual(inputs(("__import__('os') = 1",))[-1]["applicability"],"REVIEW_REQUIRED")
    def test_unproved_domain_review(self):self.assertEqual(inputs(("Symbols: x dimensionless.","x / x = 1",))[-1]["applicability"],"REVIEW_REQUIRED")
    def test_unsupported_function_review(self):self.assertEqual(inputs(("sin(x) = x",))[-1]["applicability"],"REVIEW_REQUIRED")
    def test_unsupported_matrix_review(self):self.assertEqual(inputs(("Compute the matrix inverse.",))[-1]["applicability"],"REVIEW_REQUIRED")
    def test_unsupported_prose_equation_review(self):self.assertEqual(inputs(("Calculate velocity using v = d / t.",))[-1]["applicability"],"REVIEW_REQUIRED")
    def test_bare_symbol_expression_review(self):self.assertEqual(inputs(("x + y",))[-1]["applicability"],"REVIEW_REQUIRED")
    def test_numeric_quantity_review(self):self.assertEqual(inputs(("Distance measured is 5 m.",))[-1]["applicability"],"REVIEW_REQUIRED")
    def test_subtraction_expression_review(self):self.assertEqual(inputs(("x - y",))[-1]["applicability"],"REVIEW_REQUIRED")
    def test_unformalized_arithmetic_review(self):self.assertEqual(inputs(("The addition of numbers.",))[-1]["applicability"],"REVIEW_REQUIRED")
    def test_no_math_explicit_artifact(self):self.assertEqual(inputs()[-1]["applicability"],"NOT_REQUIRED")
    def test_no_math_inventory_grounded(self):self.assertEqual(len(inputs()[-1]["source_inventory"]),len(inputs()[0]["blocks"]))
    def test_no_math_justification_persisted(self):self.assertTrue(inputs()[-1]["no_math_justification"])
    def test_no_math_not_academic_waiver(self):self.assertTrue(inputs()[-1]["requires_semantic_review"]);self.assertFalse(inputs()[-1]["product_accepted"])
    def test_foreign_anchor(self):self.bad(lambda m:m["equations"][0].update(anchor_id="foreign"))
    def test_foreign_source(self):self.bad(lambda m:m.update(source_sha256="b"*64))
    def test_foreign_document(self):self.bad(lambda m:m.update(document_artifact_id="foreign"))
    def test_foreign_knowledge(self):self.bad(lambda m:m.update(knowledge_artifact_id="foreign"))
    def test_foreign_prerequisite(self):self.bad(lambda m:m.update(prerequisite_artifact_id="foreign"))
    def test_foreign_run(self):self.bad(lambda m:m.update(run_id="foreign"))
    def test_invented_symbol(self):self.bad(lambda m:m["equations"][0].update(symbols=["invented"]))
    def test_unit_conversion(self):self.assertEqual(inputs(("1 m = 100 cm",))[-1]["equations"][0]["proof"],"EXACT_EXPLICIT_UNIT_CONVERSION")
    def test_unit_mismatch_review(self):self.assertEqual(inputs(("1 m = 1 s",))[-1]["applicability"],"REVIEW_REQUIRED")
    def test_unit_value_mismatch_review(self):self.assertEqual(inputs(("1 m = 99 cm",))[-1]["applicability"],"REVIEW_REQUIRED")
    def test_unknown_unit_review(self):self.assertEqual(inputs(("1 furlong = 1 m",))[-1]["applicability"],"REVIEW_REQUIRED")
    def test_dimension_not_physical_law(self):self.assertFalse(inputs(("1 m = 100 cm",))[-1]["equations"][0]["physical_law_proven"])
    def test_valid_explicit_derivation(self):
        m=inputs(("Step: 2 + 3 = 5 => 5 = 2 + 3",))[-1]
        self.assertEqual(m["applicability"],"REQUIRED");self.assertTrue(m["chain"]["valid"])
    def test_broken_derivation_review(self):
        m=inputs(("Step: 2 + 3 = 5 => 5 = 2 + 3","Step: 3 + 4 = 7 => 7 = 3 + 4"))[-1]
        self.assertEqual(m["applicability"],"REVIEW_REQUIRED");self.assertTrue(m["missing_steps"])
    def test_invalid_derivation_step_review(self):self.assertEqual(inputs(("Step: 2 + 3 = 5 => 5 = 7",))[-1]["applicability"],"REVIEW_REQUIRED")
    def test_math_review_cannot_unlock_reasoning(self):
        doc,k,p,b,m=inputs(("2 + 3 = 6",))
        with self.assertRaisesRegex(ProducerError,"math_review_required"):reasoning_artifact(k,p,m,b,"artifact-pr","artifact-math")
    def test_reasoning_math_reference(self):
        r=reasoning_artifact(self.k,self.p,self.m,self.b,"artifact-pr","artifact-math")
        self.assertEqual(r["math_sha256"],digest(self.m));self.assertTrue(all(any(e["artifact_id"]=="artifact-math" for e in d["evidence_refs"]) for d in r["decisions"]))
    def test_no_false_derivation_claim(self):self.assertIn("mathematical_derivation",reasoning_artifact(self.k,self.p,self.m,self.b,"artifact-pr","artifact-math")["not_executed_types"])
    def test_no_finite_probe_proof(self):self.assertNotIn("bie.math_intelligence.symbolic_equivalence",self.m["engine_identity"])
    def test_schema_rejected(self):self.bad(lambda m:m.update(schema="foreign"))
    def test_extra_field_rejected(self):self.bad(lambda m:m.update(secret="forbidden"))
    def test_applicability_forgery_rejected(self):self.bad(lambda m:m.update(applicability="NOT_REQUIRED"))
    def test_qa16_obligation_not_rewritten(self):
        rows=json.loads((ROOT/"metadata/section16/OBLIGATION_REGISTRY.json").read_text())
        gap=next(r for r in rows["records"] if r["obligation_id"]=="QA16-GAP-030")
        self.assertEqual(gap["definition"]["status"],"OPEN")
        self.assertIsNone(gap["closure_evidence"])


class DurableTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        self.credentials=Credentials();self.token=secrets.token_urlsafe(40)
        self.p=Principal("test","local",frozenset({"read","source","create","worker","control","admin_recover"}),time.time()+360)
        self.credentials.grant(self.token,self.p);self.operator=Service(self.root,self.credentials)
        self.port=MathProducerControlPlane(self.operator,enabled_profiles={PROFILE})
        self.source=self.operator.import_pdf(self.p,pdf(("2 + 3 = 5",)))
        self.run=self.port.admit(self.p,self.source["source_id"],"intent")["run_id"]
    def tearDown(self):gc.collect();self.tmp.cleanup()
    def complete(self):
        for _ in range(6):result=self.port.work_once(self.p,self.run)
        return result
    def test_six_stage_success(self):self.assertEqual(self.complete()["stages"],{s:"SUCCEEDED" for s in STAGES})
    def test_math_persisted(self):self.assertEqual(self.complete()["math"]["applicability"],"REQUIRED")
    def test_exact_reasoning_math_binding(self):
        r=self.complete();self.assertEqual(r["reasoning"]["math_sha256"],r["math"]["sha256"])
    def test_queue_acked(self):
        self.complete()
        with self.port.native(self.p,self.run,"read") as n:self.assertEqual(n.queue.stats()["ACKED"],6)
    def test_pedagogy_not_run(self):self.assertEqual(self.complete()["downstream"]["PEDAGOGY"],"NOT_RUN")
    def test_safe_projection_no_text_or_equation(self):
        raw=json.dumps(self.complete());self.assertNotIn("Birds",raw);self.assertNotIn("2 + 3",raw);self.assertNotIn(str(self.root),raw)
    def test_safe_evidence_no_text(self):
        self.complete()
        with self.port.native(self.p,self.run,"read") as n:
            for ref in n.persistence.evidence_for_run(self.run):self.assertNotIn("Birds",canonical(n.read(self.run,ref)).decode())
    def test_same_intent_replay(self):self.assertEqual(self.port.admit(self.p,self.source["source_id"],"intent")["run_id"],self.run)
    def test_conflicting_source_rejected(self):
        source=self.operator.import_pdf(self.p,pdf(("3 + 4 = 7",)))
        with self.assertRaises(Exception):self.port.admit(self.p,source["source_id"],"intent")
    def test_math_policy_intent_conflict(self):
        with self.port.native(self.p,self.run,"create") as n:
            config=profile_config();config["math_policy_version"]=2
            with self.assertRaisesRegex(ProducerError,"profile_config"):n.admit({},"local","intent",config)
    def test_restart_identity(self):
        result=self.complete();port=MathProducerControlPlane(Service(self.root,self.credentials),enabled_profiles={PROFILE})
        self.assertEqual(port.status(self.p,self.run),result)
    def test_math_cas_tamper(self):
        r=self.complete();self.operator.cas._path(r["math"]["sha256"]).write_bytes(b"tamper")
        with self.assertRaises(Exception):self.port.status(self.p,self.run)
    def test_math_foreign_run_record(self):
        r=self.complete()
        with self.port.native(self.p,self.run,"read") as n:
            with n.persistence._conn() as db:db.execute("UPDATE artifact_records SET run_id='foreign' WHERE artifact_id=?",(r["math"]["artifact_id"],))
            with self.assertRaises(ProducerError):n.status(self.run,"local")
    def test_math_tamper_blocks_reasoning(self):
        for _ in range(5):r=self.port.work_once(self.p,self.run)
        self.operator.cas._path(r["math"]["sha256"]).write_bytes(b"tamper")
        with self.assertRaises(Exception):self.port.work_once(self.p,self.run)
    def test_persisted_dependency_mismatch_rejected(self):
        with self.port.native(self.p,self.run,"read") as n:
            with n.persistence._conn() as db:db.execute("UPDATE stages SET required_predecessors_json='[]' WHERE stage_id='REASONING'")
            with self.assertRaisesRegex(ProducerError,"producer_profile_scope_mismatch"):n.work_once(self.run,"local")
    def test_task028_worker_isolated(self):
        with self.port.native(self.p,self.run,"read") as n:self.assertIsNone(n.queue.poll("wrong",capability_tags=["pdf_inspection"]))
    def test_task030_worker_isolated(self):
        with self.port.native(self.p,self.run,"read") as n:self.assertIsNone(n.queue.poll("wrong",capability_tags=["producer:"+PR_PROFILE]))
    def test_profile_explicit_enablement(self):
        with self.assertRaises(Exception):MathProducerControlPlane(self.operator).status(self.p,self.run)
    def test_inspection_profile_unchanged(self):self.assertEqual(run_options({})["profile"],"native_pdf_inspection_v1")
    def test_task029_three_stages_unchanged(self):
        port=KnowledgeProducerControlPlane(self.operator,enabled_profiles={OLD_PROFILE})
        run=port.admit(self.p,self.source["source_id"],"old")["run_id"]
        for _ in range(3):r=port.work_once(self.p,run)
        self.assertEqual(len(r["stages"]),3);self.assertTrue(r["slice_complete"])
    def test_task030_math_block_unchanged(self):
        port=ReasoningProducerControlPlane(self.operator,enabled_profiles={PR_PROFILE})
        run=port.admit(self.p,self.source["source_id"],"legacy")["run_id"]
        for _ in range(5):r=port.work_once(self.p,run)
        self.assertEqual(len(r["stages"]),5);self.assertEqual(r["safe_diagnostics"],{"REASONING":["math_evidence_required"]})
    def test_non_math_explicit_success(self):
        source=self.operator.import_pdf(self.p,pdf());run=self.port.admit(self.p,source["source_id"],"nonmath")["run_id"]
        for _ in range(6):r=self.port.work_once(self.p,run)
        self.assertTrue(r["slice_complete"]);self.assertEqual(r["math"]["applicability"],"NOT_REQUIRED")
    def test_unsupported_math_blocks(self):
        source=self.operator.import_pdf(self.p,pdf(("Compute the matrix inverse.",)));run=self.port.admit(self.p,source["source_id"],"unsupported")["run_id"]
        for _ in range(6):r=self.port.work_once(self.p,run)
        self.assertEqual(r["stages"]["MATH"],"BLOCKED");self.assertEqual(r["stages"]["REASONING"],"PENDING")
        self.assertEqual(r["math"]["applicability"],"REVIEW_REQUIRED");self.assertFalse(r["slice_complete"])
    def test_foreign_tenant(self):
        with self.port.native(self.p,self.run,"read") as n:
            with self.assertRaises(ProducerError):n.status(self.run,"foreign")
    def test_revoked_principal(self):
        self.credentials.revoke(self.token)
        with self.assertRaises(Exception):self.port.work_once(self.p,self.run)
    def test_unsupported_pause(self):
        with self.assertRaisesRegex(ProducerError,"producer_control_not_supported"):self.port.control(self.p,self.run,"pause")


if __name__=="__main__":unittest.main()
