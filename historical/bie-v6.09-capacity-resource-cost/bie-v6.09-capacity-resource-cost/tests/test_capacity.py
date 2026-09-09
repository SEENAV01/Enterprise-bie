import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from resource import resource,utilization
from quota import quota,within
from rate_limit import rate_limit,allowed
from concurrency import concurrency_limit,capacity_available
from autoscaling import autoscaling_policy,desired_instances
from budget import resource_budget,budget_defined
from cost import cost_record,cost_per_unit
from governance import resource_policy,governance_ready

def test_resource_quota():
 r=resource("s","r","CPU",100,"units",50)
 assert utilization(r)==.5
 assert within(quota("t","CPU",60,"units"),50)

def test_limits_scaling():
 rl=rate_limit("x",10,60)
 assert allowed(rl,9)
 c=concurrency_limit("x",5)
 assert capacity_available(c,4)
 p=autoscaling_policy("x",2,10,.7)
 assert desired_instances(p,.9,5)==6

def test_budget_cost_policy():
 assert budget_defined(resource_budget("s",10))
 assert cost_record("s","p",1,2,3,4)["total_cost"]==10
 assert cost_per_unit(10,2)==5
 assert governance_ready(resource_policy("s"))
