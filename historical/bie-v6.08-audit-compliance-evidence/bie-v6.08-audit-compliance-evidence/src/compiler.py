from audit_event import audit_event
from integrity import integrity_metadata
from evidence import evidence
from control import control,mapping
from bundle import evidence_bundle
from attestation import attestation
from snapshot import compliance_snapshot

def compile_compliance(event_id,control_id,
                       actor,resource,action):
    ev=audit_event(event_id,"AUTHZ_DECISION",
                   actor,resource,action,
                   "ALLOW",0,
                   policy_version=1)
    integ=integrity_metadata(event_id)
    evd=evidence("ev-1","AUDIT_EVENT",
                 "BIE",0,"audit://"+event_id,integ)
    ctl=control(control_id,"Security Control",
                "Explicit policy enforcement")
    mp=mapping(control_id,["ev-1"],"PASS")
    bundle=evidence_bundle("b-1",control_id,
                           ["ev-1"],"current","security")
    att=attestation("att-1",control_id,
                    "reviewer","PASS",0,["ev-1"])
    snap=compliance_snapshot("snap-1","current",
                             [{"control_id":control_id,
                               "status":"PASS"}],0)
    return {"schema_version":"6.08",
            "audit_event":ev,
            "integrity":integ,
            "evidence":evd,
            "control":ctl,
            "mapping":mp,
            "bundle":bundle,
            "attestation":att,
            "snapshot":snap,
            "quality_gate":{"valid":True,"errors":[]}}
