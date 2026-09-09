
class SemanticCacheError(ValueError):pass
def cosine(a,b):
 if len(a)!=len(b) or not a:raise SemanticCacheError("vector dimensions")
 import math
 na=math.sqrt(sum(x*x for x in a));nb=math.sqrt(sum(x*x for x in b))
 if na==0 or nb==0:return 0.0
 return sum(x*y for x,y in zip(a,b))/(na*nb)
def best_match(query,entries,threshold):
 hits=[(cosine(query,e["vector"]),e) for e in entries]
 hits=[x for x in hits if x[0]>=threshold]
 return max(hits,key=lambda x:x[0]) if hits else None
