
from dataclasses import dataclass
class AlertError(ValueError): pass
@dataclass(frozen=True)
class AlertRule:
 rule_id:str; metric:str; operator:str; threshold:float; severity:str; window_seconds:int
def evaluate(rule,value):
 if rule.operator not in {">",">=","<","<=","=="}: raise AlertError("operator")
 if rule.window_seconds<1: raise AlertError("window")
 if rule.severity not in {"WARNING","ERROR","CRITICAL"}: raise AlertError("severity")
 return {">":value>rule.threshold,">=":value>=rule.threshold,"<":value<rule.threshold,"<=":value<=rule.threshold,"==":value==rule.threshold}[rule.operator]
