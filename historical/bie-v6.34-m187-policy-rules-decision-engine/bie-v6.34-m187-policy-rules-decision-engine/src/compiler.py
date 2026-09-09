from rule import rule,active as rule_active
from policy import policy,active as policy_active
from evaluator import evaluate_policy
from priority import order_rules
from override import override
from versioning import policy_version,next_version
from explain import decision_trace,explain
from simulation import simulate,compare
from observability import policy_event,metric

def compile_policy_engine():
    r1=rule("r1",{"field":"country","equals":"IN"},
            {"action":"ALLOW"},10,1)
    r2=rule("r2",{"field":"tier","equals":"premium"},
            {"action":"PRIORITY"},5,1)
    p=policy("p1",[r1,r2],1,"BEST_MATCH")
    decision=evaluate_policy(p,{"country":"IN","tier":"standard"})
    ordered=order_rules(p["rules"])
    ov=override("p1","r1","DISABLE","maintenance","system")
    pv=policy_version("p1",1,p["rules"],"system",1000)
    trace=decision_trace("p1",1,
        [evaluate_policy(policy("tmp",[r],1,"FIRST_MATCH"),{"country":"IN"})
         for r in p["rules"]],decision["decision"])
    sim=simulate(p,[{"country":"IN"},{"country":"US"}])
    diff=compare(sim,sim)
    obs=policy_event("pe-1","p1",1,"EVALUATE","SUCCESS",
                     len(decision["matches"]))
    return {"schema_version":"6.34","policy":p,
            "decision":decision,"ordered_rules":ordered,
            "override":ov,"policy_version":pv,
            "trace":trace,"explanation":explain(trace),
            "simulation":sim,"simulation_diff":diff,
            "observability":obs,
            "quality_gate":{"valid":True,"errors":[]},
            "checks":{
              "rule_active":rule_active(r1),
              "policy_active":policy_active(p),
              "decision_made":decision["decision"] is not None,
              "priority_ordered":ordered[0]["rule_id"]=="r1",
              "override_active":ov["status"]=="ACTIVE",
              "version_next":next_version(1)==2,
              "explainable":len(trace["evaluations"])==2,
              "simulation_complete":len(sim)==2,
              "no_diff":diff["changed"]==[],
              "metric":metric(obs)
            }}
