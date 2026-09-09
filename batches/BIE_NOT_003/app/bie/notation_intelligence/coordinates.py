from dataclasses import dataclass
@dataclass(frozen=True)
class CoordinateSystem:
 kind:str; axes:tuple[str,...]; dimensions:int
def infer_coordinate_system(labels:set[str],context:str="")->CoordinateSystem:
 l={x.casefold() for x in labels}; c=context.casefold()
 if {"r","θ"}.issubset(labels) or "polar" in c:return CoordinateSystem("polar",("r","θ"),2)
 if {"r","θ","φ"}.issubset(labels) or "spherical" in c:return CoordinateSystem("spherical",("r","θ","φ"),3)
 if {"x","y","z"}.issubset(l):return CoordinateSystem("cartesian",("x","y","z"),3)
 if {"x","y"}.issubset(l):return CoordinateSystem("cartesian",("x","y"),2)
 return CoordinateSystem("unknown",tuple(sorted(labels)),len(labels))
