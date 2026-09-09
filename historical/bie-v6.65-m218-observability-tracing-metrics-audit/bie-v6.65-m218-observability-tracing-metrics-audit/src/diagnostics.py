def diagnose(logs,spans,metrics):
    errors=[x for x in logs if x["level"] in {"ERROR","CRITICAL"}]
    failed=[x for x in spans if x["status"]!="OK"]
    return {"error_count":len(errors),"failed_span_count":len(failed),
            "health":"DEGRADED" if errors or failed else "HEALTHY",
            "evidence":{"errors":errors,"failed_spans":failed,
                        "metrics":metrics}}
