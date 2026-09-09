def compare_models(results):
    ranked=sorted(results,
                  key=lambda x:x.get("score",0),
                  reverse=True)
    return {"ranked":ranked,
            "winner":ranked[0]["model_id"] if ranked else None}

def model_score(model_id,suite_score,cost=0,
                latency_ms=0,reliability=1.0):
    return {"model_id":model_id,"score":suite_score,
            "cost":cost,"latency_ms":latency_ms,
            "reliability":reliability}
