def experiment(experiment_id,variants,metric,
               allocation=None,guardrails=None):
    return {"experiment_id":experiment_id,"variants":variants,
            "metric":metric,"allocation":allocation or {},
            "guardrails":guardrails or {}}

def compare_variants(results,metric="effectiveness"):
    ranked=sorted(results,key=lambda x:x.get(metric,0),reverse=True)
    return {"ranking":[x.get("variant_id") for x in ranked],
            "best":ranked[0] if ranked else None}
