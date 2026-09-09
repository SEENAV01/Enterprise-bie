def model_profile(model_id,provider,capabilities,
                  quality=0.0,cost_per_unit=0.0,
                  latency_ms=0,reliability=1.0,
                  context_window=None):
    return {"model_id":model_id,"provider":provider,
            "capabilities":capabilities,
            "quality":quality,"cost_per_unit":cost_per_unit,
            "latency_ms":latency_ms,"reliability":reliability,
            "context_window":context_window}
