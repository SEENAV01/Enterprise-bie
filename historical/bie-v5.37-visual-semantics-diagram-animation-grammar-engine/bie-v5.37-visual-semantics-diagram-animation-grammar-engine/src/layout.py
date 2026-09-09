def layout_constraint(source,constraint,target=None,value=None):
    return {"source":source,"constraint":constraint,
            "target":target,"value":value}

def layout_spec(canvas,anchors=None,constraints=None):
    return {"canvas":canvas,"anchors":anchors or [],
            "constraints":constraints or []}
