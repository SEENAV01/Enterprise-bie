from dataclasses import dataclass
@dataclass(frozen=True)
class UnitCheck:
 compatible:bool; left:tuple[int,...]; right:tuple[int,...]; reason:str
def check_dimensions(left:tuple[int,...],right:tuple[int,...])->UnitCheck:
 if len(left)!=7 or len(right)!=7:raise ValueError("SI dimension vector must have 7 entries")
 ok=left==right
 return UnitCheck(ok,left,right,"dimensionally_consistent" if ok else "dimension_mismatch")
