from dataclasses import dataclass
@dataclass(frozen=True)
class StepEvidence:
 equivalent:bool; rule_known:bool; justification_present:bool
@dataclass(frozen=True)
class Validation:
 valid:bool; failures:tuple[str,...]
def validate_step(e:StepEvidence)->Validation:
 f=[]
 if not e.equivalent:f.append("not_equivalent")
 if not e.rule_known:f.append("unknown_rule")
 if not e.justification_present:f.append("missing_justification")
 return Validation(not f,tuple(f))
