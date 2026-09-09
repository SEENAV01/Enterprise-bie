def counters(events):
    out={}
    for e in events:
        key=e["type"]
        out[key]=out.get(key,0)+1
    return out

def render_metrics(events):
    starts=sum(e["type"]=="RENDER_STARTED" for e in events)
    success=sum(e["type"]=="RENDER_SUCCEEDED" for e in events)
    failed=sum(e["type"]=="RENDER_FAILED" for e in events)
    retries=sum(e["type"]=="RENDER_RETRY" for e in events)
    return {"started":starts,"succeeded":success,"failed":failed,"retries":retries,
            "success_rate":round(100*success/max(1,starts),2)}
