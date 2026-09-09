import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from rule import rule,active
from policy import policy
from evaluator import evaluate_policy
from priority import order_rules
from override import override
from versioning import next_version
from explain import decision_trace,explain
from simulation import simulate,compare

def test_rule_policy_evaluation():
 r1=rule("r1",{"field":"x","equals":1},{"allow":True},10)
 r2=rule("r2",{"field":"x","equals":2},{"allow":False},5)
 p=policy("p",[r1,r2],1,"BEST_MATCH")
 d=evaluate_policy(p,{"x":1})
 assert active(r1) and d["decision"]=={"allow":True}

def test_priority_override_version():
 r1=rule("a",{"field":"x","equals":1},{"a":1},1)
 r2=rule("b",{"field":"x","equals":1},{"b":1},5)
 assert order_rules([r1,r2])[0]["rule_id"]=="b"
 assert override("p","r1","OFF","test","system")["status"]=="ACTIVE"
 assert next_version(3)==4

def test_explain_simulation():
 p=policy("p",[rule("r",{"field":"x","equals":1},{"ok":1})])
 d=simulate(p,[{"x":1},{"x":2}])
 t=decision_trace("p",1,[{"rule_id":"r","matched":True}],d[0]["decision"])
 assert explain(t)["matched_rules"]==["r"]
 assert compare(d,d)["changed"]==[]
