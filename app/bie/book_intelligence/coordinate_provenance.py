class E(ValueError):pass
def to_pixels(box,w,h):
 if w<=0 or h<=0 or len(box)!=4:raise E("geometry")
 x1,y1,x2,y2=box
 if not(0<=x1<x2<=1 and 0<=y1<y2<=1):raise E("box")
 return tuple(round(v) for v in (x1*w,y1*h,x2*w,y2*h))
