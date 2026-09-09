def box(x=0,y=0,width=0,height=0):
    return {"x":x,"y":y,"width":width,"height":height}

def center(b):
    return {"x":b["x"]+b["width"]/2,"y":b["y"]+b["height"]/2}

def intersects(a,b,gap=0):
    return not (a["x"]+a["width"]+gap <= b["x"] or
                b["x"]+b["width"]+gap <= a["x"] or
                a["y"]+a["height"]+gap <= b["y"] or
                b["y"]+b["height"]+gap <= a["y"])
