from dependencies import validate_dependencies
from validation import validate_contract

def compile_production_system(assets,contracts,nodes,edges):
    asset_ids={a["asset_id"] for a in assets}
    errors=[]
    for c in contracts:
        if c.get("asset_ref") not in asset_ids:
            errors.append("CONTRACT_ASSET_REFERENCE_MISSING")
        errors.extend(validate_contract(c))
    errors.extend(validate_dependencies(nodes,edges))
    return {"schema_version":"5.49",
            "assets":assets,"contracts":contracts,
            "dependency_graph":{"nodes":nodes,"edges":edges},
            "quality_gate":{"valid":not errors,
                            "errors":sorted(set(errors))}}
