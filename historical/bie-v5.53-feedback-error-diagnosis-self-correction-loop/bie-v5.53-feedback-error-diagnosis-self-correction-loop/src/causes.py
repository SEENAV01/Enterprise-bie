def root_cause(cause_id,layer,cause,signals=None,
               upstream_refs=None):
    return {"cause_id":cause_id,"layer":layer,"cause":cause,
            "signals":signals or {},"upstream_refs":upstream_refs or []}

def rank_causes(causes):
    return sorted(causes,
                  key=lambda c:c.get("confidence",0),reverse=True)
