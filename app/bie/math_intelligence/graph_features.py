from dataclasses import dataclass
@dataclass(frozen=True)
class GraphFeatures:
 roots:tuple[float,...]; y_intercept:float|None; extrema:tuple[tuple[float,float],...]; monotonic:str
def analyze_samples(points:list[tuple[float,float]])->GraphFeatures:
 if not points:raise ValueError("no samples")
 p=sorted(points); roots=tuple(x for x,y in p if abs(y)<1e-12)
 yi=next((y for x,y in p if abs(x)<1e-12),None)
 ext=[]
 for i in range(1,len(p)-1):
  if (p[i][1]>p[i-1][1] and p[i][1]>p[i+1][1]) or (p[i][1]<p[i-1][1] and p[i][1]<p[i+1][1]):ext.append(p[i])
 ys=[y for _,y in p]
 mono="increasing" if all(a<=b for a,b in zip(ys,ys[1:])) else "decreasing" if all(a>=b for a,b in zip(ys,ys[1:])) else "mixed"
 return GraphFeatures(roots,yi,tuple(ext),mono)
