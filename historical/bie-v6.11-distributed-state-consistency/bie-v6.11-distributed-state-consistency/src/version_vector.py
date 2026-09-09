def version_vector(nodes=None):
    return {n:int(v) for n,v in (nodes or {}).items()}

def increment(vector,node):
    out=dict(vector)
    out[node]=out.get(node,0)+1
    return out

def dominates(a,b):
    keys=set(a)|set(b)
    return all(a.get(k,0)>=b.get(k,0) for k in keys)

def concurrent(a,b):
    return not dominates(a,b) and not dominates(b,a)
