from dataclasses import dataclass

class SceneIRValidationError(ValueError): pass

@dataclass(frozen=True)
class ValidationIssue:
    code:str
    path:str
    message:str
    severity:str="ERROR"
    owner:str="DSL"

@dataclass(frozen=True)
class ValidationReport:
    validator_id:str
    issues:tuple[ValidationIssue,...]
    passed:bool
    review_required:bool=True
    accepted:bool=False

def issue(code,path,message,severity="ERROR",owner="DSL"):
    return ValidationIssue(code,path,message,severity,owner)

def report(validator_id,issues):
    issues=tuple(issues)
    return ValidationReport(validator_id,issues,not any(i.severity=="ERROR" for i in issues),True,False)

def require_pass(r):
    if not r.passed:
        raise SceneIRValidationError(f"{r.validator_id} failed")
    return True
