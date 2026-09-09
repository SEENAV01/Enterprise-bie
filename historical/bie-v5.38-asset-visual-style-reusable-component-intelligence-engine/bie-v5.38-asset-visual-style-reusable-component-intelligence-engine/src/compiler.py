from selection import select_assets,component_compatibility

def compile_visual_system(style_system,assets,components,instances,
                          templates=None):
    asset_ids={a["asset_id"] for a in assets}
    component_ids={c["component_id"] for c in components}
    errors=[]
    for i in instances:
        if i.get("component_id") not in component_ids:
            errors.append("MISSING_COMPONENT_REFERENCE")
    for c in components:
        for a in c.get("asset_refs",[]):
            if a not in asset_ids:
                errors.append("MISSING_ASSET_REFERENCE")
    return {"schema_version":"5.38",
            "style_system":style_system,
            "assets":assets,"components":components,
            "instances":instances,"templates":templates or [],
            "quality_gate":{"valid":not errors,
                            "errors":sorted(set(errors))}}
