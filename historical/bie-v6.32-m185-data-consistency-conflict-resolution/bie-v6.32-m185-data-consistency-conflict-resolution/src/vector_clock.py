def vector_clock(entries=None):
    return dict(entries or {})

def increment(clock,node_id):
    out=dict(clock); out[node_id]=out.get(node_id,0)+1; return out

def dominates(a,b):
    keys=set(a)|set(b)
    return all(a.get(k,0)>=b.get(k,0) for k in keys) and any(a.get(k,0)>b.get(k,0) for k in keys)

def concurrent(a,b):
    return not dominates(a,b) and not dominates(b,a) and a!=b
