from .space_common import *
def make_box(x,y,width,height):
    return NormalizedBox(x,y,width,height)
def normalized_point(x,y):
    return (unit(x,"x"),unit(y,"y"))
def denormalize_point(point,canvas_width,canvas_height):
    w=num(canvas_width,"canvas_width");h=num(canvas_height,"canvas_height")
    if w<=0 or h<=0:raise SpaceIRError("canvas dimensions must be >0")
    x,y=normalized_point(*point)
    return (x*w,y*h)
