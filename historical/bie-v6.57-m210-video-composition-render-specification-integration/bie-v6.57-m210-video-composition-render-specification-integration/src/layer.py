SUPPORTED_LAYERS = {
    "BACKGROUND","VISUAL","TEXT","EQUATION","NARRATION","AUDIO",
    "CAPTION","OVERLAY","TRANSITION"
}

def layer(layer_id, layer_type, source_ref, start_sec=0, duration_sec=None,
          z_index=0, properties=None):
    if layer_type not in SUPPORTED_LAYERS:
        raise ValueError("UNSUPPORTED_LAYER_TYPE")
    return {"layer_id":layer_id,"layer_type":layer_type,
            "source_ref":source_ref,"start_sec":start_sec,
            "duration_sec":duration_sec,"z_index":z_index,
            "properties":properties or {}}

def valid(x):
    return bool(x["layer_id"] and x["source_ref"] and
                x["layer_type"] in SUPPORTED_LAYERS)
