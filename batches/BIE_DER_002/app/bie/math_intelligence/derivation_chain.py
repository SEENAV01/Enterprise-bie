from dataclasses import dataclass
@dataclass(frozen=True)
class Step:
 before:str; after:str
@dataclass(frozen=True)
class ChainResult:
 valid:bool; breaks:tuple[int,...]; start:str|None; end:str|None
def validate_chain(steps:list[Step])->ChainResult:
 if not steps:return ChainResult(False,(),"", "")
 breaks=tuple(i for i in range(1,len(steps)) if steps[i-1].after.strip()!=steps[i].before.strip())
 return ChainResult(not breaks,breaks,steps[0].before,steps[-1].after)
