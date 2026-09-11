"""RE-TEMP-043 — Canonical fingerprint for reproducible temporal reasoning inputs."""
import hashlib,json
def temporal_fingerprint(payload):
    def norm(v):
        if isinstance(v,dict): return {str(k):norm(v[k]) for k in sorted(v,key=str)}
        if isinstance(v,(list,tuple)): return [norm(x) for x in v]
        if isinstance(v,set): return sorted((norm(x) for x in v),key=lambda x:json.dumps(x,sort_keys=True))
        if isinstance(v,(str,int,float,bool)) or v is None:return v
        raise TypeError("unsupported fingerprint value")
    raw=json.dumps(norm(payload),sort_keys=True,separators=(",",":"),ensure_ascii=False)
    return hashlib.sha256(raw.encode()).hexdigest()
