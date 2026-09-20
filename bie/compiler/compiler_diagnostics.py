from __future__ import annotations
from dataclasses import dataclass

SEVERITIES=("ERROR","WARNING","INFO")
RANK={"ERROR":0,"WARNING":1,"INFO":2}

@dataclass(frozen=True)
class CompilerDiagnostic:
    code:str
    severity:str
    stage:str
    message:str
    path:str="$"
    owner:str="COMP"
    remediation:str|None=None

    def __post_init__(self):
        for name in ("code","stage","message","path","owner"):
            value=getattr(self,name)
            if not isinstance(value,str) or not value.strip():
                raise ValueError(f"{name} invalid")
        if self.severity not in SEVERITIES:
            raise ValueError("severity invalid")
        if self.remediation is not None and (not isinstance(self.remediation,str) or not self.remediation.strip()):
            raise ValueError("remediation invalid")

@dataclass(frozen=True)
class CompilerDiagnosticReport:
    diagnostics:tuple[CompilerDiagnostic,...]
    error_count:int
    warning_count:int
    info_count:int
    passed:bool
    accepted:bool=False

def make_diagnostic(code,severity,stage,message,path="$",owner="COMP",remediation=None):
    return CompilerDiagnostic(code,severity,stage,message,path,owner,remediation)

def build_diagnostic_report(diagnostics):
    unique={}
    for d in diagnostics:
        key=(d.code,d.severity,d.stage,d.path,d.message)
        unique[key]=d
    ordered=tuple(sorted(
        unique.values(),
        key=lambda d:(RANK[d.severity],d.stage,d.code,d.path,d.message)
    ))
    errors=sum(d.severity=="ERROR" for d in ordered)
    warnings=sum(d.severity=="WARNING" for d in ordered)
    infos=sum(d.severity=="INFO" for d in ordered)
    return CompilerDiagnosticReport(ordered,errors,warnings,infos,errors==0,False)

def diagnostic_from_exception(exc,stage,path="$"):
    return CompilerDiagnostic(
        "COMP_EXCEPTION","ERROR",str(stage),str(exc) or exc.__class__.__name__,
        str(path),"COMP","Inspect the owning compiler stage and input contract."
    )

def require_no_errors(report):
    if not report.passed:
        raise ValueError("compiler diagnostics contain errors")
    return True
