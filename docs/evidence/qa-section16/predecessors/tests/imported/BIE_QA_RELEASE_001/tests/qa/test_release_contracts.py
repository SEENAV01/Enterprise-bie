import unittest
from bie.qa.release_contracts import *

def ev(gate,status="PASS",eid=None):
    return GateEvidence(
        evidence_id=eid or f"ev-{gate}",
        gate_id=gate,
        status=status,
        evaluator="test-evaluator",
        evaluator_version="1.0.0",
        inspected_artifact_refs=["artifact-1"],
        evidence_artifact_refs=[f"evidence:{gate}"],
        summary="checked",
        diagnostics=[] if status=="PASS" else ["failed check"],
        remediation_layer="QA"
    )

class ReleaseContractTests(unittest.TestCase):
    def test_default_policy_requires_runtime_gates(self):
        p=enterprise_default_policy(True,True)
        p.validate()
        by={g.gate_id:g.mode for g in p.gates}
        for g in ["code_compile","video_render","rendered_frame_inspection","game_build","game_runtime","game_learning_alignment"]:
            self.assertEqual(by[g],"REQUIRED")

    def test_success_only_when_all_required_pass(self):
        p=enterprise_default_policy(True,True)
        evidence=[ev(g.gate_id) for g in p.gates if g.mode=="REQUIRED"]
        d=ReleaseEvaluator.evaluate(p,evidence)
        self.assertEqual(d.release_status,"SUCCESS")

    def test_missing_required_evidence_blocks(self):
        p=enterprise_default_policy(True,False)
        evidence=[ev(g.gate_id) for g in p.gates if g.mode=="REQUIRED" and g.gate_id!="video_render"]
        d=ReleaseEvaluator.evaluate(p,evidence)
        self.assertEqual(d.release_status,"BLOCKED")
        self.assertIn("video_render",d.blocking_gates)

    def test_fail_blocks_release(self):
        p=enterprise_default_policy(False,False)
        evidence=[ev(g.gate_id) for g in p.gates if g.mode=="REQUIRED"]
        evidence=[ev("source_grounding","FAIL") if e.gate_id=="source_grounding" else e for e in evidence]
        d=ReleaseEvaluator.evaluate(p,evidence)
        self.assertEqual(d.release_status,"BLOCKED")

    def test_required_skipped_is_error(self):
        p=enterprise_default_policy(False,False)
        evidence=[ev(g.gate_id) for g in p.gates if g.mode=="REQUIRED"]
        evidence=[ev("lineage_integrity","SKIPPED") if e.gate_id=="lineage_integrity" else e for e in evidence]
        d=ReleaseEvaluator.evaluate(p,evidence)
        self.assertEqual(d.release_status,"BLOCKED")

    def test_video_disabled_does_not_require_video_runtime(self):
        p=enterprise_default_policy(False,True)
        by={g.gate_id:g.mode for g in p.gates}
        self.assertNotIn("video_render",by)
        self.assertIn("game_runtime",by)

    def test_game_disabled_does_not_require_game_runtime(self):
        p=enterprise_default_policy(True,False)
        by={g.gate_id:g.mode for g in p.gates}
        self.assertNotIn("game_runtime",by)
        self.assertIn("video_render",by)

    def test_human_review_policy_prevents_success(self):
        p=enterprise_default_policy(False,False)
        p=ReleasePolicy(p.policy_id,p.policy_version,p.enable_video,p.enable_game,p.gates,require_human_review=True)
        evidence=[ev(g.gate_id) for g in p.gates if g.mode=="REQUIRED"]
        d=ReleaseEvaluator.evaluate(p,evidence)
        self.assertEqual(d.release_status,"READY_FOR_REVIEW")

    def test_lineage_always_required(self):
        p=enterprise_default_policy(False,False)
        gates=[g for g in p.gates if g.gate_id!="lineage_integrity"]
        bad=ReleasePolicy("x","1.0.0",False,False,gates)
        with self.assertRaises(ReleaseContractError): bad.validate()

    def test_source_grounding_always_required(self):
        p=enterprise_default_policy(False,False)
        gates=[g for g in p.gates if g.gate_id!="source_grounding"]
        bad=ReleasePolicy("x","1.0.0",False,False,gates)
        with self.assertRaises(ReleaseContractError): bad.validate()

if __name__=="__main__": unittest.main()
