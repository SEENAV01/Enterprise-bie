from __future__ import annotations
from dataclasses import dataclass
from .compiler_asset_common import *

@dataclass(frozen=True)
class MissingAssetDiagnostic:
    code:str
    severity:str
    asset_ref:str
    element_id:str
    message:str

@dataclass(frozen=True)
class MissingAssetReport:
    diagnostics:tuple[MissingAssetDiagnostic,...]
    missing_count:int
    passed:bool
    accepted:bool=False

def detect_missing_assets(document,path_registry):
    diagnostics=[]
    for element in document.elements:
        props=dict(element.props)
        asset_ref=props.get("asset_ref")
        if not asset_ref:
            continue
        result=path_registry.resolve(str(asset_ref))
        if not result.passed:
            diagnostics.append(MissingAssetDiagnostic(
                "COMP_ASSET_MISSING",
                "ERROR",
                str(asset_ref),
                element.element_id,
                "Required asset could not be resolved for compiler output."
            ))
    diagnostics=tuple(sorted(
        diagnostics,
        key=lambda d:(d.element_id,d.asset_ref,d.code)
    ))
    return MissingAssetReport(
        diagnostics,
        len(diagnostics),
        not diagnostics,
        False
    )

def require_no_missing_assets(report):
    if not report.passed:
        details=";".join(
            f"{d.element_id}:{d.asset_ref}" for d in report.diagnostics
        )
        raise CompilerAssetError("missing compiler assets:"+details)
    return True
