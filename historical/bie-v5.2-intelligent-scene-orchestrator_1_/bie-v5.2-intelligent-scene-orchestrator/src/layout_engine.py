from geometry import rect,overlaps,clamp
from hierarchy import rank_objects

def auto_layout(objects,canvas_w=1920,canvas_h=1080,gap=24):
    ordered=rank_objects(objects)
    placements=[]
    x=80;y=100;row_h=0
    for o in ordered:
        w=float(o.get("width",400)); h=float(o.get("height",180))
        if x+w>canvas_w-80:
            x=80;y+=row_h+gap;row_h=0
        r=clamp(rect(x,y,w,h),{"w":canvas_w,"h":canvas_h})
        placements.append({**o,"rect":r})
        x+=w+gap;row_h=max(row_h,h)
    return placements

def collision_report(placements,padding=12):
    collisions=[]
    for i,a in enumerate(placements):
        for b in placements[i+1:]:
            if overlaps(a["rect"],b["rect"],padding):
                collisions.append((a["id"],b["id"]))
    return collisions
