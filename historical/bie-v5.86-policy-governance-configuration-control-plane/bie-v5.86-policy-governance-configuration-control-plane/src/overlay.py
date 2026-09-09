def merge(base,overlay):
    result=dict(base)
    for key,value in overlay.items():
        if isinstance(value,dict) and isinstance(result.get(key),dict):
            result[key]=merge(result[key],value)
        else:
            result[key]=value
    return result

def effective_policy(base,environment_overlay=None,
                     tenant_overlay=None):
    result=merge(base,environment_overlay or {})
    return merge(result,tenant_overlay or {})
