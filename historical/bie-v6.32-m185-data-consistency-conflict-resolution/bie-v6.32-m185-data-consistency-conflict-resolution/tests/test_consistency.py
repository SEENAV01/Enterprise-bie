import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
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

def test_clocks_and_versions():
 assert tick(logical_clock("a",1))["counter"]==2
 v=state_version("x",increment(vector_clock({"a":1}),"a"))
 assert versioned(v) and dominates(v["clock"],{"a":1})

def test_conflict_merge_tombstone():
 c=conflict("k",{"v":1},{"v":2})
 assert detected(c)
 assert resolve(c,merge_policy("MULTI_VALUE"))==[{"v":1},{"v":2}]
 assert deleted(tombstone("k",{"a":2}))

def test_reconciliation_convergence():
 assert complete(anti_entropy("a","b"))["status"]=="COMPLETED"
 assert applied(reconciliation("k",1,2))["status"]=="APPLIED"
 assert not converged(divergence("k","a","b",1))
 assert concurrent({"a":1},{"b":1})
 assert allows_read(consistency_contract("CAUSAL"),5)

def test_observability():
 e=consistency_event("e","k","MERGE","OK",1,2)
 assert metric(e)["merge_count"]==2
