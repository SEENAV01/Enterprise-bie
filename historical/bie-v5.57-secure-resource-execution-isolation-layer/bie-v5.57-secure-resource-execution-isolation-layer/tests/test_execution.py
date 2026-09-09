import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from compiler import compile_execution

def test_allowed():
 e={"budgets":{"cpu_seconds":100}}
 u={"cpu_seconds":20}
 i={"no_host_access":True,"no_privilege_escalation":True,
    "readonly_inputs":True,"restricted_outputs":True}
 assert compile_execution(e,u,i)["quality_gate"]["allowed"]

def test_budget_fail():
 e={"budgets":{"cpu_seconds":10}}
 u={"cpu_seconds":20}
 i={"no_host_access":True,"no_privilege_escalation":True,
    "readonly_inputs":True,"restricted_outputs":True}
 assert not compile_execution(e,u,i)["quality_gate"]["allowed"]
