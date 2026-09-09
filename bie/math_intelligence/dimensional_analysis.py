from dataclasses import dataclass
@dataclass(frozen=True)
class Dimension:
 L:int=0; M:int=0; T:int=0; I:int=0; Theta:int=0; N:int=0; J:int=0
BASE={"m":Dimension(L=1),"kg":Dimension(M=1),"s":Dimension(T=1),"A":Dimension(I=1),"K":Dimension(Theta=1),"mol":Dimension(N=1),"cd":Dimension(J=1)}
def combine(a:Dimension,b:Dimension,power:int=1)->Dimension:
 return Dimension(*(getattr(a,k)+power*getattr(b,k) for k in ("L","M","T","I","Theta","N","J")))
def dimension_of(terms:list[tuple[str,int]])->Dimension:
 d=Dimension()
 for u,p in terms:
  if u not in BASE:raise ValueError("unknown base unit")
  d=combine(d,BASE[u],p)
 return d
