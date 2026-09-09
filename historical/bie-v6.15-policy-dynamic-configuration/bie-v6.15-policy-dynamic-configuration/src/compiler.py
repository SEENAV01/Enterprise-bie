from rule import rule
from evaluator import evaluate
from composition import compose
from config import config,activate
from feature_flag import feature_flag,active
from rollout import rollout,advance
from validation import validation,passed
from rollback import rollback,approve
from change_audit import change_audit

def compile_policy():
    rules=[
      rule("r1","workflow.read","ALLOW",100,"tenant-a"),
      rule("r2","workflow.read","DENY",10,"tenant-a")]
    ev=evaluate(rules,"workflow.read")
    comp=compose(["r1","r2"],"OR")
    cfg=activate(config("workflow",
                         3,{"timeout":30},"tenant-a"))
    flag=feature_flag("new-engine",True,25,"tenant-a")
    ro=advance(rollout(3,"CANARY",0),25)
    va=validation("workflow-v3",3,
                   [{"name":"schema","passed":True},
                    {"name":"policy","passed":True}],True)
    rb=approve(rollback(2,"failed-canary","operator"))
    audit=change_audit("chg-1","workflow",
                       2,3,"operator","canary")
    return {"schema_version":"6.15",
            "rules":rules,
            "decision":ev,
            "composition":comp,
            "configuration":cfg,
            "feature_flag":flag,
            "rollout":ro,
            "validation":va,
            "rollback":rb,
            "change_audit":audit,
            "quality_gate":{"valid":True,"errors":[]}}
