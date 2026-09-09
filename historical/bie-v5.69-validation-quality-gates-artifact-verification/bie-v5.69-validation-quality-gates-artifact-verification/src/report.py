from results import summarize
from gates import evaluate_gate

def verification_report(artifact_id,results,gates):
    gate_results=[evaluate_gate(results,g) for g in gates]
    return {"schema_version":"5.69",
            "artifact_id":artifact_id,
            "results":results,
            "summary":summarize(results),
            "gates":gate_results,
            "release_eligible":all(x["passed"] for x in gate_results)}
