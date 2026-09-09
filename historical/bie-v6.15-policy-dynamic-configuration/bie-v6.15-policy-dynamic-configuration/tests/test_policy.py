import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from rule import rule
from evaluator import evaluate,validate_decision
from composition import compose
from config import config,activate
from feature_flag import feature_flag,active
from rollout import rollout,advance
from validation import validation,passed
from rollback import rollback,approve
from change_audit import change_audit

def test_rules():
 rs=[rule("low","x","DENY",1),
     rule("high","x","ALLOW",10)]
 assert evaluate(rs,"x")["decision"]=="ALLOW"
 assert validate_decision("DENY")

def test_config_flag_rollout():
 assert activate(config("x",1))["status"]=="ACTIVE"
 assert active(feature_flag("f",True,50),25)
 assert advance(rollout(1),10)["percentage"]==10
 assert compose(["a"],"AND")["operator"]=="AND"

def test_validation_rollback_audit():
 v=validation("x",1,[{"passed":True}],True)
 assert passed(v)
 assert approve(rollback(1,"r","u"))["status"]=="APPROVED"
 assert change_audit("c","x",1,2,"u","r")["to_version"]==2
