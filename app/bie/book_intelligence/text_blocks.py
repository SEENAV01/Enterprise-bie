
from dataclasses import dataclass
class TextBlockError(ValueError):pass
@dataclass(frozen=True)
class TextBlock:block_id:str;text:str;region_ids:tuple;page:int;confidence:float
def build(block_id,text,region_ids,page,confidence):
 if not block_id or not str(text).strip() or not region_ids:raise TextBlockError("missing block data")
 if page<1 or not 0<=confidence<=1:raise TextBlockError("page/confidence")
 if len(set(region_ids))!=len(region_ids):raise TextBlockError("duplicate regions")
 return TextBlock(block_id,str(text).strip(),tuple(region_ids),page,float(confidence))
