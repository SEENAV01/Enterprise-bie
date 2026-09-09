import unittest
from bie.reasoning.decision_contracts import (
    ReasoningDecision, EvidenceRef, DecisionAlternative,
    ReasoningDecisionGraph, ReasoningContractError, decision_payload
)

def base(**overrides):
    data = dict(
        decision_id="d1",
        decision_type="teaching_order",
        subject_id="concept:coulomb",
        question="What comes first?",
        selected_option="phenomenon-first",
        rationale_summary="Ground observable behavior before symbolic abstraction.",
        confidence=0.9,
        evidence_refs=[EvidenceRef("artifact-source-1","primary",0.95)],
        alternatives=[DecisionAlternative("formula-first","Start with equation",0.5,"Too abstract")],
        premises=["Learner understands signed numbers"],
        constraints=["Preserve physics correctness"],
        uncertainty=[],
        downstream_effects=["PED","DIR","VIS"],
        depends_on_decisions=[],
        requires_review=False,
        policy_tags=["critical"],
    )
    data.update(overrides)
    return ReasoningDecision(**data)

class ReasoningContractTests(unittest.TestCase):
    def test_valid_decision(self):
        d=base()
        d.validate(critical=True)
        self.assertEqual(decision_payload(d)["selected_option"],"phenomenon-first")

    def test_invalid_type_fails(self):
        with self.assertRaises(ReasoningContractError):
            base(decision_type="magic_reasoning").validate()

    def test_evidence_required(self):
        with self.assertRaises(ReasoningContractError):
            base(evidence_refs=[]).validate()

    def test_low_confidence_critical_requires_review(self):
        with self.assertRaises(ReasoningContractError):
            base(confidence=0.7, requires_review=False).validate(critical=True)
        base(confidence=0.7, requires_review=True).validate(critical=True)

    def test_below_auto_threshold_requires_review(self):
        with self.assertRaises(ReasoningContractError):
            base(confidence=0.4, requires_review=False).validate()
        base(confidence=0.4, requires_review=True).validate()

    def test_graph_dependency_and_ancestors(self):
        d1=base(decision_id="d1")
        d2=base(decision_id="d2", decision_type="representation_selection", depends_on_decisions=["d1"])
        g=ReasoningDecisionGraph([d1,d2])
        g.validate()
        self.assertEqual([d.decision_id for d in g.ancestors("d2")],["d1"])

    def test_missing_dependency_fails(self):
        g=ReasoningDecisionGraph([base(depends_on_decisions=["missing"])])
        with self.assertRaises(ReasoningContractError):
            g.validate()

    def test_cycle_fails(self):
        d1=base(decision_id="d1",depends_on_decisions=["d2"])
        d2=base(decision_id="d2",depends_on_decisions=["d1"])
        g=ReasoningDecisionGraph([d1,d2])
        with self.assertRaises(ReasoningContractError):
            g.validate()

if __name__=="__main__":
    unittest.main()
