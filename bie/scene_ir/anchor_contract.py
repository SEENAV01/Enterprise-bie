from dataclasses import dataclass
from .space_common import *
@dataclass(frozen=True)
class Anchor:
    anchor_id:str
    element_id:str
    kind:str
    x:float
    y:float
    def __post_init__(self):
        object.__setattr__(self,"anchor_id",tok(self.anchor_id,"anchor_id"))
        object.__setattr__(self,"element_id",tok(self.element_id,"element_id"))
        if self.kind not in {"center","top","bottom","left","right","top_left","top_right","bottom_left","bottom_right","custom"}:
            raise SpaceIRError("unsupported anchor kind")
        object.__setattr__(self,"x",unit(self.x,"x"))
        object.__setattr__(self,"y",unit(self.y,"y"))
def anchor_for_box(anchor_id,element_id,kind,box):
    pts={
      "center":(box.x+box.width/2,box.y+box.height/2),
      "top":(box.x+box.width/2,box.y),
      "bottom":(box.x+box.width/2,box.y+box.height),
      "left":(box.x,box.y+box.height/2),
      "right":(box.x+box.width,box.y+box.height/2),
      "top_left":(box.x,box.y),"top_right":(box.x+box.width,box.y),
      "bottom_left":(box.x,box.y+box.height),"bottom_right":(box.x+box.width,box.y+box.height)
    }
    if kind=="custom":raise SpaceIRError("custom anchor requires explicit coordinates")
    x,y=pts[kind]
    return Anchor(anchor_id,element_id,kind,x,y)
