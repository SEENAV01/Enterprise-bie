def validation_check(check_id,kind,target,rule,
                    severity="required",metadata=None):
    return {"check_id":check_id,"kind":kind,"target":target,
            "rule":rule,"severity":severity,"metadata":metadata or {}}

def check_kinds():
    return ["SCHEMA","PROVENANCE","VISUAL","AUDIO","TIMING",
            "INTERACTION","PEDAGOGICAL","ACCESSIBILITY","CONTENT",
            "DETERMINISM","RENDER"]
