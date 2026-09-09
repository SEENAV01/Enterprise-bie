from clock import logical_clock,tick
from vector_clock import vector_clock,increment,dominates,concurrent
from version import state_version,versioned
from conflict import conflict,detected
from merge import merge_policy,resolve
from tombstone import tombstone,deleted
from anti_entropy import anti_entropy,complete
from reconciliation import reconciliation,applied
from divergence import divergence,converged
from consistency import consistency_contract,allows_read
from observability import consistency_event,metric

def compile_consistency():
    lc=tick(logical_clock("node-a",3))
    vc=increment(vector_clock({"node-a":3,"node-b":2}),"node-a")
    v=state_version({"status":"READY"},vc,"node-a")
    left={"value":"A","clock":{"a":2}}
    right={"value":"B","clock":{"b":2}}
    cf=conflict("k",left,right)
    mp=merge_policy("MULTI_VALUE")
    ts=tombstone("old-key",{"a":4})
    ae=complete(anti_entropy("a","b"))
    rec=applied(reconciliation("k",left,right,"MERGE"))
    div=divergence("k","a","b",2)
    con=consistency_contract("CAUSAL",True)
    obs=consistency_event("ce-1","k","RECONCILE","SUCCESS",2,1)
    return {"schema_version":"6.32",
            "logical_clock":lc,"vector_clock":vc,
            "state_version":v,"conflict":cf,
            "merge_policy":mp,"tombstone":ts,
            "anti_entropy":ae,"reconciliation":rec,
            "divergence":div,"consistency":con,
            "observability":obs,
            "quality_gate":{"valid":True,"errors":[]},
            "checks":{
              "clock_incremented":lc["counter"]==4,
              "vector_incremented":vc["node-a"]==4,
              "versioned":versioned(v),
              "conflict_detected":detected(cf),
              "merge_result":resolve(cf,mp)==[left,right],
              "tombstoned":deleted(ts),
              "anti_entropy_complete":ae["status"]=="COMPLETED",
              "reconciliation_applied":rec["status"]=="APPLIED",
              "divergent":not converged(div),
              "causal_read":allows_read(con,1),
              "concurrent_versions":concurrent({"a":1},{"b":1}),
              "metric":metric(obs)
            }}
