from math import hypot
def analyze(a,b):
 if len(a)!=2 or len(b)!=2:raise ValueError("2D coordinates required")
 dx=b[0]-a[0];dy=b[1]-a[1]
 return {"dx":dx,"dy":dy,"distance":hypot(dx,dy),"direction":("right" if dx>0 else "left" if dx<0 else "same_x", "up" if dy>0 else "down" if dy<0 else "same_y")}
