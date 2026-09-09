def reusable_component(component_id,name,component_type,
                       semantic_contract=None,asset_refs=None,
                       style_ref=None):
    return {"component_id":component_id,"name":name,
            "component_type":component_type,
            "semantic_contract":semantic_contract or {},
            "asset_refs":asset_refs or [],
            "style_ref":style_ref}

def component_instance(instance_id,component_id,props=None,
                        overrides=None):
    return {"instance_id":instance_id,"component_id":component_id,
            "props":props or {},"overrides":overrides or {}}
