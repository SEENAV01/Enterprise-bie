def media_layer(ref, media_type, fit="contain", position=None):
    return {
        "ref":ref,
        "type":media_type,
        "fit":fit,
        "position":position or {"x":0.5,"y":0.5},
        "z_index":0
    }

def compose(layers):
    return {"layers":layers,"ordering":"z_index_then_declaration"}
