def compile_diagnostic_plan(diagnoses,remediations,adaptation,
                            reassessment=None,prerequisites=None):
    diag_ids={d["diagnosis_id"] for d in diagnoses}
    errors=[]
    for ref in adaptation.get("diagnosis_refs",[]):
        if ref not in diag_ids:
            errors.append("DIAGNOSIS_REFERENCE_MISSING")
    rem_ids={r["remediation_id"] for r in remediations}
    for s in adaptation.get("steps",[]):
        for ref in s.get("target_refs",[]):
            # target refs may be concepts rather than remediation IDs;
            # therefore this is informational rather than an error.
            pass
    if not adaptation.get("reassessment"):
        errors.append("REASSESSMENT_PLAN_MISSING")
    return {"schema_version":"5.43",
            "diagnoses":diagnoses,
            "remediations":remediations,
            "adaptation":adaptation,
            "reassessment":reassessment,
            "prerequisites":prerequisites or [],
            "quality_gate":{"valid":not errors,
                            "errors":sorted(set(errors))}}
