def layout_region(region_id,x,y,w,h,anchor="center"):
    return {"region_id":region_id,"x":x,"y":y,"width":w,"height":h,
            "anchor":anchor}

def default_layout():
    return {
      "canvas":{"width":1920,"height":1080},
      "regions":[
        layout_region("main",80,100,1760,800),
        layout_region("top",80,40,1760,100),
        layout_region("bottom",80,900,1760,120)
      ]
    }
