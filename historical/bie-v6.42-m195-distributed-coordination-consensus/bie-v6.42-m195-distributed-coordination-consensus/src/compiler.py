from participant import participant,active
from epoch import epoch,current
from lease import lease,held_by
from leader import leader_term,is_leader
from quorum import quorum,reached
from prepare import prepare,prepared
from accept import accept,accepted
from finalize import finalize,finalized
from membership import membership,contains
from audit import coordination_event,successful
from observability import coordination_metric,healthy

def compile_coordination():
    members=["node-a","node-b","node-c"]
    p=participant("node-a","coord://node-a")
    ep=epoch(7,"epoch-7")
    ls=lease("lease-7","node-a",999999,True)
    lt=leader_term(7,"node-a","epoch-7")
    q=quorum(members)
    pr=prepare("coord-1","node-a",7,"proposal-1")
    ac=accept("coord-1","node-a",7,"proposal-1")
    fn=finalize("coord-1",7,"proposal-1","COMMITTED")
    mem=membership("epoch-7",members,"STABLE")
    ev=coordination_event("ce-1","coord-1","FINALIZE","SUCCESS","node-a")
    met=coordination_metric("cm-1","coord-1",7,"FINALIZE","SUCCESS",31,True)
    return {"schema_version":"6.42","participant":p,"epoch":ep,
            "lease":ls,"leader_term":lt,"quorum":q,
            "prepare":pr,"accept":ac,"finalize":fn,
            "membership":mem,"audit":ev,"observability":met,
            "quality_gate":{"valid":True,"errors":[]},
            "checks":{
              "participant_active":active(p),
              "epoch_current":current(ep,7),
              "lease_holder":held_by(ls,"node-a"),
              "leader_valid":is_leader(lt,"node-a"),
              "quorum_reached":reached(q,["node-a","node-b"]),
              "prepared":prepared(pr),
              "accepted":accepted(ac),
              "finalized":finalized(fn),
              "membership_contains":contains(mem,"node-c"),
              "audit_success":successful(ev),
              "observability_healthy":healthy(met)
            }}
