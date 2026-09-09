def production_contract(contract_id,asset_ref,renderer_class=None,
                       inputs=None,outputs=None,timing=None,
                       interaction=None,accessibility=None,
                       validation=None,constraints=None):
    return {"contract_id":contract_id,"asset_ref":asset_ref,
            "renderer_class":renderer_class,
            "inputs":inputs or [],"outputs":outputs or [],
            "timing":timing or {},"interaction":interaction or {},
            "accessibility":accessibility or {},
            "validation":validation or [],
            "constraints":constraints or []}

def contract_requirements(contract):
    return {
      "has_asset":bool(contract.get("asset_ref")),
      "has_output":bool(contract.get("outputs")),
      "has_validation":bool(contract.get("validation"))
    }
