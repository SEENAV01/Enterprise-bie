
from dataclasses import dataclass
class VisionError(ValueError):pass
@dataclass(frozen=True)
class VisionInput:data_ref:str;mime_type:str;width:int|None=None;height:int|None=None
def validate(v):
 if not v.data_ref or not v.mime_type.startswith("image/"):raise VisionError("image input required")
 if v.width is not None and v.width<1:raise VisionError("width")
 if v.height is not None and v.height<1:raise VisionError("height")
 return True
