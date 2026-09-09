import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from config import config_value,typed
from scope import scope,hierarchy
from defaults import default,resolve
from validation import rule,validate
from secret_ref import secret_ref,is_reference
from reload import reload_policy,hot_reload
from feature_flag import feature_flag,enabled
from rollout import rollout,applies
from policy import policy,evaluate
from observability import config_event,metric

def test_config_scope_defaults_validation():
 c=config_value("x",1,"integer")
 assert typed(c)
 assert hierarchy([scope("G",priority=0),
                   scope("W",priority=10)])[0]["name"]=="W"
 assert resolve(None,3)==3
 assert validate(10,rule("x",True,None,1,20))

def test_secret_reload_flags_rollout_policy():
 assert is_reference(secret_ref("x"))
 assert hot_reload(reload_policy("ON_CHANGE",False))
 f=feature_flag("x")
 assert enabled(f,True)
 assert applies(rollout("x","PERCENTAGE",50),25)
 assert evaluate(policy("p","ALLOW"),{})

def test_observability():
 e=config_event("e","x","SET","APPLIED","GLOBAL","FILE")
 assert metric(e)["status"]=="APPLIED"
