from dataclasses import dataclass
@dataclass(frozen=True)
class Interval:
 lower:float|None; upper:float|None; lower_closed:bool=False; upper_closed:bool=False
def contains(i:Interval,x:float)->bool:
 lo=True if i.lower is None else x>i.lower or (i.lower_closed and x==i.lower)
 hi=True if i.upper is None else x<i.upper or (i.upper_closed and x==i.upper)
 return lo and hi
def validate_interval(i:Interval):
 if i.lower is not None and i.upper is not None and i.lower>i.upper:raise ValueError("reversed interval")
 if i.lower==i.upper and not(i.lower_closed and i.upper_closed):raise ValueError("empty interval")
 return i
