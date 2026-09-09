def provenance(job_id, composition_ids=None,
               render_profile_ids=None, qa_report_ids=None,
               upstream_artifacts=None):
    return {"job_id":job_id,
            "composition_ids":composition_ids or [],
            "render_profile_ids":render_profile_ids or [],
            "qa_report_ids":qa_report_ids or [],
            "upstream_artifacts":upstream_artifacts or []}

def traceable(p):
    return bool(p["composition_ids"] and
                (p["render_profile_ids"] or p["qa_report_ids"] or
                 p["upstream_artifacts"]))
