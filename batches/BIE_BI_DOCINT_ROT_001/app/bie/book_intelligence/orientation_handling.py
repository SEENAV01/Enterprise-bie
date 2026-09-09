class E(ValueError):pass
ANGLES=(0,90,180,270)
def normalize(angle,width,height):
 if angle not in ANGLES or width<=0 or height<=0:raise E("orientation")
 rotated=angle in (90,270)
 return {"rotation":angle,"logical_width":height if rotated else width,"logical_height":width if rotated else height}
