def evaluate(render,complexity,quality):
    checks={
      "accuracy_budget":quality.get("accuracy") in {"HIGH","EXTREME"},
      "strategy_fit":render.get("strategy") is not None,
      "resource_fit":complexity.get("score",0)>=0
    }
    return {"checks":checks,"passed":all(checks.values())}
