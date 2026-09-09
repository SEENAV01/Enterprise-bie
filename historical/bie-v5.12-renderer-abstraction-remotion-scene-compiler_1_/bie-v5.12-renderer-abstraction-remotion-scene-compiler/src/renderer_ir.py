def scene_ir(scene_id,width=1920,height=1080,fps=30):
    return {"scene_id":scene_id,"canvas":{"width":width,"height":height,"fps":fps},
            "layers":[],"animations":[],"audio":[],"captions":[],"transitions":[]}

def add_layer(ir,layer_id,component,props=None,z_index=0):
    ir["layers"].append({"layer_id":layer_id,"component":component,
                         "props":props or {},"z_index":z_index})
    return ir

def add_animation(ir,target_id,property_name,keyframes,easing="linear"):
    ir["animations"].append({"target_id":target_id,"property":property_name,
                              "keyframes":keyframes,"easing":easing})
    return ir
