def failure_summary(events):
    failures={}
    for e in events:
        if e["level"]=="ERROR" or e["type"].endswith("_FAILED"):
            code=e.get("payload",{}).get("code",e["type"])
            failures[code]=failures.get(code,0)+1
    return sorted([{"code":k,"count":v} for k,v in failures.items()],
                  key=lambda x:(-x["count"],x["code"]))

def scope_summary(events, scope):
    grouped={}
    for e in events:
        sid=e.get("payload",{}).get(scope)
        if sid: grouped.setdefault(sid,[]).append(e)
    return {k:render_scope(v) for k,v in grouped.items()}

def render_scope(events):
    return {"events":len(events),
            "errors":sum(e["level"]=="ERROR" for e in events)}
