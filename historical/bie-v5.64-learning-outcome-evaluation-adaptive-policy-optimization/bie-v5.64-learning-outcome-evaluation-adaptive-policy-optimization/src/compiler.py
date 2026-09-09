from evaluation import evaluate_outcome,aggregate_outcomes
from adaptation import adaptation_signal

def compile_learning_evaluation(outcomes,thresholds=None):
    evaluated=[evaluate_outcome(o,thresholds) for o in outcomes]
    signals=[adaptation_signal({**o,"delta":o.get("delta",{})})
             for o in outcomes]
    return {"schema_version":"5.64",
            "evaluations":evaluated,
            "aggregate":aggregate_outcomes(evaluated),
            "adaptation_signals":signals,
            "quality_gate":{"valid":True,"errors":[]}}
