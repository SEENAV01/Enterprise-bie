def qa_report(report_id, job_id, checks, overall_status,
              artifact_refs=None):
    if overall_status not in {"PASS","FAIL","REVIEW"}:
        raise ValueError("INVALID_QA_REPORT_STATUS")
    return {"report_id":report_id,"job_id":job_id,"checks":checks,
            "overall_status":overall_status,
            "artifact_refs":artifact_refs or []}

def passed(report):
    return report["overall_status"]=="PASS" and all(
        c["status"]=="PASS" for c in report["checks"])
