def timing_requirement(start=None,duration=None,fps=None,
                       sync_refs=None):
    return {"start":start,"duration":duration,"fps":fps,
            "sync_refs":sync_refs or []}
