def generation_plan(asset_type,subject,requirements,
                    preferred_method=None):
    methods={"diagram":"VECTOR_TEMPLATE","animation":"MOTION_TEMPLATE",
             "simulation":"PROCEDURAL_SIMULATION","3d":"PROCEDURAL_3D",
             "image":"IMAGE_TEMPLATE","video":"COMPOSITING_TEMPLATE"}
    method=preferred_method or methods.get(asset_type,"GENERIC_TEMPLATE")
    return {"asset_type":asset_type,"subject":subject,
            "requirements":requirements,"method":method}

def valid(p):
    return bool(p["asset_type"] and p["subject"] and p["method"])
