def provenance(loop_id, render_job_ids=None,
               failure_ids=None, diagnosis_ids=None,
               remediation_ids=None, qa_report_ids=None,
               upstream_artifacts=None):
    return {"loop_id":loop_id,
            "render_job_ids":render_job_ids or [],
            "failure_ids":failure_ids or [],
            "diagnosis_ids":diagnosis_ids or [],
            "remediation_ids":remediation_ids or [],
            "qa_report_ids":qa_report_ids or [],
            "upstream_artifacts":upstream_artifacts or []}

def traceable(p):
    return bool(p["failure_ids"] and p["diagnosis_ids"] and
                p["remediation_ids"])
