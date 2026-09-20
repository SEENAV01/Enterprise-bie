class SceneIRCapabilityError(ValueError): pass

def tok(v,n):
    if not isinstance(v,str) or not v.strip(): raise SceneIRCapabilityError(f"{n} blank")
    return v.strip()

def ids(values,n,allow_empty=False):
    out=tuple(tok(x,n) for x in (values or ()))
    if not allow_empty and not out: raise SceneIRCapabilityError(f"{n} required")
    if len(set(out))!=len(out): raise SceneIRCapabilityError(f"{n} duplicates")
    return out
