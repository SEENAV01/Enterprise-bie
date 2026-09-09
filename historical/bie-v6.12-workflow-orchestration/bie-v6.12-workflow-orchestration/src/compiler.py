from workflow import workflow,pause,resume
from state_machine import state_machine,transition
from checkpoint import checkpoint
from timer import timer,fire
from wait import wait_condition,satisfy
from saga import saga_step,complete,compensate
from cancellation import cancellation,approve
from approval import approval_gate,approve as gate_approve
from compensation import compensation_plan
from determinism import deterministic_input,replay_order

def compile_workflow():
    w=resume(pause(workflow("wf-1",
        "Order Fulfillment",1,"tenant-a")))
    sm=state_machine(
        ["START","RUNNING","DONE"],
        {("START","BEGIN"):"RUNNING",
         ("RUNNING","FINISH"):"DONE"},
        "START")
    tr=transition(sm,"START","BEGIN")
    cp=checkpoint("wf-1",1,"RUNNING",0)
    tm=fire(timer("tm-1","wf-1",10,"wait"),10)
    wt=satisfy(wait_condition("wait-1","wf-1",
                              "payment.confirmed",20))
    sg=complete(saga_step("reserve","reserve_inventory",
                           "release_inventory"))
    cn=approve(cancellation("wf-1","operator","incident"))
    gate=gate_approve(
        approval_gate("gate-1","wf-1",
                      ["manager"],1),"manager")
    comp=compensation_plan("wf-1",
                            ["release_inventory"])
    events=replay_order([
        deterministic_input("wf-1",2,"PAYMENT","p2"),
        deterministic_input("wf-1",1,"ORDER","p1")])
    return {"schema_version":"6.12",
            "workflow":w,"state_machine":sm,
            "transition":tr,"checkpoint":cp,
            "timer":tm,"wait":wt,"saga_step":sg,
            "cancellation":cn,"approval_gate":gate,
            "compensation_plan":comp,
            "deterministic_replay":events,
            "quality_gate":{"valid":True,"errors":[]}}
