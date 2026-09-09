def layout_constraint(target,kind,value,
                    priority="REQUIRED"):
    return {"target":target,"kind":kind,
            "value":value,"priority":priority}

def layout_spec(constraints=None,viewport=None):
    return {"constraints":constraints or [],
            "viewport":viewport or {}}
