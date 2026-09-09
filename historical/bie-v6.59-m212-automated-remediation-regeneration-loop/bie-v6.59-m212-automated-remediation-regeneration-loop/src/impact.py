def impact_analysis(analysis_id, failed_refs,
                   preserve_refs=None, rerender_scope=None,
                   dependency_refs=None):
    return {"analysis_id":analysis_id,"failed_refs":failed_refs,
            "preserve_refs":preserve_refs or [],
            "rerender_scope":rerender_scope or [],
            "dependency_refs":dependency_refs or []}

def minimal_scope(a):
    return bool(a["failed_refs"] and a["rerender_scope"])
