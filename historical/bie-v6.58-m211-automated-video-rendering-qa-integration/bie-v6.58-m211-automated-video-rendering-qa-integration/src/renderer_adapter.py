def renderer_adapter(adapter_id, engine, version,
                     capabilities=None):
    return {"adapter_id":adapter_id,"engine":engine,"version":version,
            "capabilities":capabilities or []}

def valid(a):
    return bool(a["adapter_id"] and a["engine"] and a["version"])
