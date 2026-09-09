def provenance(report_id, artifact_refs=None,
               source_script_ids=None, storyboard_ids=None,
               evidence_ids=None, remediation_signal_ids=None):
    return {"report_id":report_id,"artifact_refs":artifact_refs or [],
            "source_script_ids":source_script_ids or [],
            "storyboard_ids":storyboard_ids or [],
            "evidence_ids":evidence_ids or [],
            "remediation_signal_ids":remediation_signal_ids or []}

def traceable(p):
    return bool(p["report_id"] and p["artifact_refs"] and
                (p["source_script_ids"] or p["storyboard_ids"]))
