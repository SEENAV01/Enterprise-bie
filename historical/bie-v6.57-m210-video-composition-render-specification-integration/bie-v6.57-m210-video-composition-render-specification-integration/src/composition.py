from layer import layer, valid as layer_valid

def composition(comp_id, storyboard_id, layers,
                 width=1920, height=1080, fps=30,
                 duration_sec=None, background=None):
    if not layers:
        raise ValueError("COMPOSITION_REQUIRES_LAYERS")
    return {"composition_id":comp_id,"storyboard_id":storyboard_id,
            "layers":layers,"width":width,"height":height,"fps":fps,
            "duration_sec":duration_sec,"background":background}

def valid(c):
    return bool(c["composition_id"] and c["storyboard_id"] and c["layers"]
                and all(layer_valid(x) for x in c["layers"]))
