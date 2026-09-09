def safe_area(canvas_width,canvas_height,margin):
    return {"x":margin,"y":margin,
            "width":max(0,canvas_width-2*margin),
            "height":max(0,canvas_height-2*margin)}

def inside_safe_area(b,area):
    return (b["x"]>=area["x"] and b["y"]>=area["y"] and
            b["x"]+b["width"]<=area["x"]+area["width"] and
            b["y"]+b["height"]<=area["y"]+area["height"])
