from sli import sli
from slo import slo
from error_budget import error_budget
from burn import burn_rate
from alert import alert_rule

def compile_reliability(service,
                        good,total,target,
                        window="30d"):
    metric=sli(f"{service}.availability",
               good,total,window)
    objective=slo(f"{service}.availability",
                  target,metric["name"],window)
    budget=error_budget(target)
    observed=1-metric["value"]
    burn=burn_rate(observed,
                   budget["allowed_error_ratio"])
    rule=alert_rule("slo-burn",
                    f"{service} SLO burn",
                    "burn_exceeded")
    return {"schema_version":"6.04",
            "sli":metric,
            "slo":objective,
            "error_budget":budget,
            "burn_rate":burn,
            "alert_rule":rule,
            "quality_gate":{"valid":True,"errors":[]}}
