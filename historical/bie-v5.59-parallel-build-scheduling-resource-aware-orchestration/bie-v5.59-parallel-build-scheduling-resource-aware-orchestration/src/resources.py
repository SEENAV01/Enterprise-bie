def resource_pool(cpu=0,gpu=0,memory_mb=0,tools=None):
    return {"cpu":cpu,"gpu":gpu,"memory_mb":memory_mb,
            "tools":tools or {}}

def fits(required,available):
    for k,v in required.items():
        if k=="tools":
            for t,n in v.items():
                if available.get("tools",{}).get(t,0)<n: return False
        elif available.get(k,0)<v:
            return False
    return True

def reserve(available,required):
    out={**available,"tools":dict(available.get("tools",{}))}
    for k,v in required.items():
        if k=="tools":
            for t,n in v.items(): out["tools"][t]=out["tools"].get(t,0)-n
        else: out[k]=out.get(k,0)-v
    return out
