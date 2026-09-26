import unittest
from bie.game_engine.contracts import *

def state():
    return [StateVariable("x","number",1.0,0,10,units="m")]
def manip():
    return [Manipulable("m","Mover","object",{"x":"x"},["drag_x"],"controller",accessibility_label="Mover")]
def rule():
    return [Rule("r","x changed",[Effect("x","set",1.0)],"Grounded update",concept_refs=["c"])]
def challenge(**kw):
    d=dict(challenge_id="c1",title="Challenge",mission_prompt="Do it",mechanic="manipulate_parameter",
           success_condition="x==2",allowed_actions=["drag_x"],hints=[Hint("h","Try moving it",1)],
           feedback=FeedbackPolicy("Yes","No"),mastery_weight=1.0,difficulty=.5,
           concept_refs=["concept"],reasoning_decision_refs=["reason"])
    d.update(kw); return Challenge(**d)
def level(**kw):
    d=dict(level_id="l1",title="Level",purpose="Learn",state_variables=state(),manipulables=manip(),
           rules=rule(),challenges=[challenge()],reasoning_decision_refs=["reason"],learning_objective_refs=["lo"])
    d.update(kw); return GameLevel(**d)

class GameIRTests(unittest.TestCase):
    def test_valid_level(self): level().validate()
    def test_keyword_independent_mechanic(self):
        challenge(mechanic="timeline_reconstruction").validate()
    def test_bad_state_binding_fails(self):
        m=Manipulable("m","Mover","object",{"x":"missing"},["drag"],"controller",accessibility_label="Mover")
        with self.assertRaises(GameIRContractError): level(manipulables=[m]).validate()
    def test_rule_effect_target_fails(self):
        rr=Rule("r","event",[Effect("missing","set",1)],"why",concept_refs=["c"])
        with self.assertRaises(GameIRContractError): level(rules=[rr]).validate()
    def test_challenge_requires_reason_trace(self):
        with self.assertRaises(GameIRContractError): challenge(reasoning_decision_refs=[]).validate()
    def test_challenge_requires_learning_target(self):
        with self.assertRaises(GameIRContractError): challenge(concept_refs=[],learning_objective_refs=[]).validate()
    def test_invalid_mechanic_fails(self):
        with self.assertRaises(GameIRContractError): challenge(mechanic="topic_keyword_game").validate()
    def test_adaptation_contract(self):
        level(adaptations=[AdaptationRule("a","attempts>2","remediate","bridge")]).validate()
    def test_game_document_requires_source_and_reasoning_trace(self):
        exp=GameExperience("g","Game","revision",[level()],{},{"threshold":.8})
        with self.assertRaises(GameIRContractError): GameDocument("1.0.0","d",[exp],[],["r"]).validate()
        with self.assertRaises(GameIRContractError): GameDocument("1.0.0","d",[exp],["s"],[]).validate()
    def test_multiple_domain_mechanics(self):
        for mech in ["simulation_experiment","timeline_reconstruction","map_interaction","equation_balance","diagnose_error"]:
            challenge(mechanic=mech).validate()

if __name__=="__main__":unittest.main()
