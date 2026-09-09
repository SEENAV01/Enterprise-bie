import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))

from lesson_job import lesson_job,valid
from orchestrator import LessonOrchestrator
from states import can_transition
from state_event import state_event
from artifact_registry import artifact,valid as artifact_valid
from stage_contract import satisfied
from checkpoint import checkpoint,resumable
from failure_policy import failure_policy,should_fail
from provenance import provenance,traceable
from verification import verification,passed

def test_happy_path():
    j=lesson_job("j","source","output")
    o=LessonOrchestrator(j)
    o.run_happy_path()
    assert valid(j) and o.state=="VERIFIED"
    assert can_transition("QA_EVALUATED","VERIFIED")

def test_contracts_and_resume():
    a=artifact("a","script","uri","SCRIPTED")
    e=state_event("e","j","PLANNED","SCRIPTED","complete")
    cp=checkpoint("cp","j","SCRIPTED",["a"],1)
    p=provenance("j",["source"],["e"],["a"],["cp"])
    v=verification("v","j","VERIFIED","PASS",["e"],"output")
    policy=failure_policy(3,True)
    assert artifact_valid(a) and e["to_state"]=="SCRIPTED"
    assert satisfied("SCRIPTED",["script"]) and resumable(cp)
    assert traceable(p) and passed(v)
    assert should_fail("CRITICAL",0,policy)
