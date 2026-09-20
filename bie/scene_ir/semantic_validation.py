from .validation_common import *

ALLOWED_ELEMENT_TYPES={
 "text","equation","shape","vector","diagram","graph","chart","map","timeline",
 "image","video","simulation","model2d","model3d","annotation","callout","highlight","particle_system"
}
ALLOWED_ACTIONS={
 "enter","exit","emphasize","reveal","transform","morph","trace","path_follow",
 "camera","simulation_state","static_focus","static_trace","crossfade_states",
 "state_snapshots","progressive_static_trace","path_endpoints_with_progress_marker"
}

def validate_semantics(doc):
    issues=[]
    for i,e in enumerate(doc.get("elements",())):
        et=e.get("element_type")
        if et not in ALLOWED_ELEMENT_TYPES:
            issues.append(issue("UNKNOWN_ELEMENT_TYPE",f"$.elements[{i}].element_type",f"Unsupported element type {et}"))
        if et=="equation":
            props=e.get("props",{})
            if not props.get("expression"):
                issues.append(issue("EQUATION_EMPTY",f"$.elements[{i}].props.expression","Equation expression required"))
        if et in {"image","video","model3d"}:
            props=e.get("props",{})
            if not props.get("asset_ref"):
                issues.append(issue("ASSET_REF_MISSING",f"$.elements[{i}].props.asset_ref","Asset-backed element requires asset_ref"))
    for i,t in enumerate(doc.get("tracks",())):
        action=t.get("action")
        if action not in ALLOWED_ACTIONS:
            issues.append(issue("UNKNOWN_ACTION",f"$.tracks[{i}].action",f"Unsupported action {action}"))
    return report("DSL-VALID-SEMANTIC",issues)
