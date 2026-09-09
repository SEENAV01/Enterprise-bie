from entity import entity
from concurrency import update_if_version
from sequence import sequence
from version_vector import version_vector,increment
from transaction import transaction,commit
from idempotent_transition import transition
from consistency import consistency_contract
from conflict import conflict,resolve
from reconciliation import reconciliation,mark

def compile_state():
    e=entity("entity-1","WORKFLOW","tenant-a",{"status":"READY"},7)
    update=update_if_version(e,7,{"status":"RUNNING"})
    seq=sequence("entity-1",8)
    vv=increment(version_vector({"node-a":3}),"node-a")
    tx=commit(transaction("tx-1",[{"op":"update",
                                  "entity_id":"entity-1"}]))
    tr=transition({"status":"RUNNING"},"op-1",
                  "COMPLETE",{"status":"DONE"})
    consistency=consistency_contract(
        "workflow-state","CAUSAL",True,True)
    cf=resolve(conflict("entity-1",7,8,
                         {"status":"A"},{"status":"B"}),
               {"status":"B"},"LAST_WRITER_WINS")
    rec=mark(reconciliation("entity-1",
                             {"status":"B"},
                             {"status":"B"},0),"CONVERGED")
    return {"schema_version":"6.11",
            "entity":e,
            "update":update,
            "sequence":seq,
            "version_vector":vv,
            "transaction":tx,
            "idempotent_transition":tr,
            "consistency":consistency,
            "conflict":cf,
            "reconciliation":rec,
            "quality_gate":{"valid":True,"errors":[]}}
