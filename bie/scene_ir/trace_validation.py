from .validation_common import *

def _check_lineage(obj,path,issues):
    if not obj.get("source_refs"):
        issues.append(issue("SOURCE_TRACE_MISSING",path+".source_refs","source_refs required",owner="PROVENANCE"))
    if not obj.get("reasoning_refs"):
        issues.append(issue("REASONING_TRACE_MISSING",path+".reasoning_refs","reasoning_refs required",owner="REASONING"))

def validate_source_reasoning_trace(doc):
    issues=[]
    _check_lineage(doc,"$",issues)
    for i,e in enumerate(doc.get("elements",())):
        _check_lineage(e,f"$.elements[{i}]",issues)
    for i,t in enumerate(doc.get("tracks",())):
        _check_lineage(t,f"$.tracks[{i}]",issues)
    return report("DSL-VALID-TRACE",issues)
