from run_manager import create_run,transition
from operator import command_allowed
from approval import request_approval,decide
from gates import deployment_gate,release_gate
from audit import audit_action,validate_chain

def build_m265_runtime():
    run=create_run("run-course-001","course")
    audit=[]
    before=run["state"]; transition(run,"QUEUED","scheduler"); audit.append(audit_action(run["run_id"],"scheduler","QUEUE",before,run["state"]))
    before=run["state"]; transition(run,"RUNNING","worker"); audit.append(audit_action(run["run_id"],"worker","START",before,run["state"]))
    assert command_allowed(run["state"],"PAUSE")
    before=run["state"]; transition(run,"PAUSED","operator","maintenance"); audit.append(audit_action(run["run_id"],"operator","PAUSE",before,run["state"]))
    before=run["state"]; transition(run,"RUNNING","operator"); audit.append(audit_action(run["run_id"],"operator","RESUME",before,run["state"]))
    before=run["state"]; transition(run,"COMPLETED","worker"); audit.append(audit_action(run["run_id"],"worker","COMPLETE",before,run["state"]))
    before=run["state"]; transition(run,"AWAITING_APPROVAL","system"); audit.append(audit_action(run["run_id"],"system","REQUEST_RELEASE",before,run["state"]))
    approval=request_approval(run["run_id"])
    decision=decide(approval,"APPROVE","release-manager","QA and artifact checks passed")
    gate=deployment_gate(True,decision["request"]["decision"]=="APPROVE",True,True)
    release=release_gate(run,gate)
    if release["allowed"]:
        before=run["state"]; transition(run,"RELEASED","release-manager"); audit.append(audit_action(run["run_id"],"release-manager","RELEASE",before,run["state"]))
    audit_check=validate_chain(audit)
    final={"schema_version":"7.12","run":run,"approval":approval,
           "approval_decision":decision,"deployment_gate":gate,
           "release_gate":release,"audit":audit,"audit_validation":audit_check}
    final["control_plane_gate"]={"valid":run["state"]=="RELEASED" and audit_check["valid"],
                                 "errors":[] if run["state"]=="RELEASED" and audit_check["valid"] else ["CONTROL_PLANE_BLOCKED"]}
    return final
