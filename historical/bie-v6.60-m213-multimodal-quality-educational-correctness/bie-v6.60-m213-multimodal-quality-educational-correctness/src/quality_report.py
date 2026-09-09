def quality_report(report_id, artifact_ref, modality_scores,
                  correctness_checks, objectives, alignment_records,
                  overall_score, decision_value, issues=None):
    return {"report_id":report_id,"artifact_ref":artifact_ref,
            "modality_scores":modality_scores,
            "correctness_checks":correctness_checks,
            "objectives":objectives,
            "alignment_records":alignment_records,
            "overall_score":overall_score,
            "decision":decision_value,"issues":issues or []}

def passed(r):
    return r["decision"] == "PASS"
