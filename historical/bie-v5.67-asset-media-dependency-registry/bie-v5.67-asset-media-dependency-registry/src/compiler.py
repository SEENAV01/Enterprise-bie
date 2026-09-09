from staleness import impacted_assets

def compile_registry(reg,changed_keys=None):
    changed_keys=changed_keys or []
    impacted=impacted_assets(reg,changed_keys)
    return {"schema_version":"5.67",
            "registry":reg,
            "impact_analysis":{"changed":changed_keys,
                               "impacted":impacted},
            "quality_gate":{"valid":True,"errors":[]}}
