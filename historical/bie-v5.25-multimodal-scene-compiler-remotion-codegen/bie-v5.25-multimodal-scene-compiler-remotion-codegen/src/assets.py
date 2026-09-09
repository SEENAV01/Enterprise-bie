def asset_binding(asset_id,kind,source=None,props=None):
    return {"asset_id":asset_id,"kind":kind,"source":source,
            "props":props or {}}

def bind_assets(bindings):
    return {"bindings":bindings}
