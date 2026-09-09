def rect(x,y,w,h):
    return {"x":x,"y":y,"w":w,"h":h}

def overlaps(a,b,padding=0):
    return not (
      a["x"]+a["w"]+padding <= b["x"] or
      b["x"]+b["w"]+padding <= a["x"] or
      a["y"]+a["h"]+padding <= b["y"] or
      b["y"]+b["h"]+padding <= a["y"]
    )

def clamp(r,canvas):
    return {
      "x":max(0,min(r["x"],canvas["w"]-r["w"])),
      "y":max(0,min(r["y"],canvas["h"]-r["h"])),
      "w":r["w"],"h":r["h"]
    }
