import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from workflow import workflow,pause,resume
from state_machine import state_machine,transition
from checkpoint import checkpoint,latest
from timer import timer,fire
from wait import wait_condition,satisfy
from saga import saga_step,complete
from cancellation import cancellation,approve
from approval import approval_gate,approve as gate_approve
from compensation import compensation_plan,start
from determinism import deterministic_input,replay_order

def test_workflow_state_machine():
 w=resume(pause(workflow("w","x")))
 assert w["status"]=="RUNNING"
 m=state_machine(["A","B"],{("A","GO"):"B"},"A")
 assert transition(m,"A","GO")["state"]=="B"
 assert transition(m,"B","GO")["status"]=="REJECTED"

def test_checkpoint_timer_wait():
 cps=[checkpoint("w",1,"A",1),checkpoint("w",2,"B",2)]
 assert latest(cps)["sequence"]==2
 assert fire(timer("t","w",10),10)["status"]=="FIRED"
 assert satisfy(wait_condition("x","w","ok"))["status"]=="SATISFIED"

def test_saga_cancel_approval():
 assert complete(saga_step("s","a","undo"))["status"]=="COMPLETED"
 assert approve(cancellation("w","u"))["status"]=="APPROVED"
 g=approval_gate("g","w",["a"],1)
 assert gate_approve(g,"a")["status"]=="APPROVED"
 assert start(compensation_plan("w",[]))["status"]=="RUNNING"

def test_deterministic_replay():
 xs=[deterministic_input("w",2,"B","b"),
     deterministic_input("w",1,"A","a")]
 assert replay_order(xs)[0]["sequence"]==1
