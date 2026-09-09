from dataclasses import dataclass
@dataclass(frozen=True)
class CaseResult:
 case_id:str; domain:str; passed:bool; failures:tuple[str,...]
REQUIRED={"physics","mathematics","chemistry"}
def evaluate_case(case_id,domain,grounded,formula_ok,derivation_ok,units_ok):
 if not case_id.strip() or not domain.strip():raise ValueError("case metadata required")
 f=[]
 if not grounded:f.append("grounding")
 if not formula_ok:f.append("formula")
 if not derivation_ok:f.append("derivation")
 if not units_ok:f.append("units")
 return CaseResult(case_id,domain,not f,tuple(f))
def summarize(results):
 domains={r.domain for r in results};missing=tuple(sorted(REQUIRED-domains))
 passed=sum(r.passed for r in results)
 return {"cases":len(results),"passed":passed,"pass_rate":passed/len(results) if results else 0.0,"missing_domains":missing}
