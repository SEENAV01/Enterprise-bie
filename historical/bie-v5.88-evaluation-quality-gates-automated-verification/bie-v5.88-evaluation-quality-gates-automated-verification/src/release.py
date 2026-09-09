def release_eligibility(gate_results,regression_ok=True,
                        confidence=1.0,min_confidence=0.0):
    gates_ok=all(x["passed"] for x in gate_results)
    return {"eligible":gates_ok and regression_ok
            and confidence>=min_confidence,
            "gates_ok":gates_ok,
            "regression_ok":regression_ok,
            "confidence_ok":confidence>=min_confidence}
